import json
import os
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
CACHE_DIR = os.path.join(BASE_DIR, "cache", "suse")
INSTALLED_PATH = os.path.join(CACHE_DIR, "installed.json")
MATCHED_PATH = os.path.join(CACHE_DIR, "matched.json")
BATCH_RESULTS_DIR = os.path.join(CACHE_DIR, "batch_results")
BATCH_SIZE = 400


def ensure_cache_dir() -> None:
    global CACHE_DIR, INSTALLED_PATH, MATCHED_PATH, BATCH_RESULTS_DIR
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        os.makedirs(BATCH_RESULTS_DIR, exist_ok=True)
    except PermissionError:
        # Fallback to user's home directory if cache dir is not writable
        CACHE_DIR = os.path.join(os.path.expanduser("~"), ".ophiron_cache", "suse")
        INSTALLED_PATH = os.path.join(CACHE_DIR, "installed.json")
        MATCHED_PATH = os.path.join(CACHE_DIR, "matched.json")
        BATCH_RESULTS_DIR = os.path.join(CACHE_DIR, "batch_results")
        os.makedirs(CACHE_DIR, exist_ok=True)
        os.makedirs(BATCH_RESULTS_DIR, exist_ok=True)


def _parse_rpm_output(output: str) -> List[Dict[str, str]]:
    """Parse rpm -qa output into list of packages with name and version"""
    packages: List[Dict[str, str]] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        # rpm -qa --queryformat prints: NAME\tVERSION-RELEASE
        parts = line.split('\t')
        if len(parts) == 2:
            name, version = parts
            packages.append({"name": name, "version": version})
    return packages


def get_installed_packages(use_system: bool = True) -> List[Dict[str, str]]:
    """Get all installed packages using rpm command (SUSE uses rpm like Fedora)"""
    ensure_cache_dir()
    if use_system:
        try:
            completed = subprocess.run(
                ['rpm', '-qa', '--queryformat', '%{NAME}\t%{VERSION}-%{RELEASE}\n'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
            packages = _parse_rpm_output(completed.stdout)
            payload = {"packages": packages, "timestamp": datetime.utcnow().isoformat()}
            try:
                with open(INSTALLED_PATH, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False)
            except PermissionError:
                # If we can't write to the installed file, just continue without caching
                pass
            return packages
        except Exception:
            # Fall back to cache if available
            pass

    if os.path.exists(INSTALLED_PATH):
        with open(INSTALLED_PATH, "r", encoding="utf-8") as f:
            obj = json.load(f)
            return obj.get("packages", [])

    return []


def _parse_zypper_list_patches_cve(output: str) -> List[Dict[str, Any]]:
    """
    Parse 'zypper list-patches --cve' output.
    
    Example output format:
    Issue | No.           | Patch                       | Category | Severity | Interactive | Status | Since | Summary
    ------+---------------+-----------------------------+----------+----------+-------------+--------+-------+--------------------------
    cve   | CVE-2025-7039 | openSUSE-SLE-15.6-2025-4308 | security | moderate | ---         | needed | -     | Security update for glib2
    """
    import logging
    logger = logging.getLogger(__name__)
    
    patches = []
    lines = output.splitlines()
    
    logger.debug("Parsing zypper list-patches --cve output, %d lines", len(lines))
    
    # Skip header lines (usually first 2-3 lines)
    start_idx = 0
    for i, line in enumerate(lines):
        if '|' in line and ('cve' in line.lower() or 'CVE' in line or 'patch' in line.lower() or 'issue' in line.lower()):
            # Check if this is a header separator line (contains dashes)
            if '---' in line or '===' in line:
                start_idx = i + 1
                logger.debug("Found separator line at index %d, starting parse from index %d", i, start_idx)
                break
            # Check if this is the actual header
            if i == 0 or i == 1:
                start_idx = i + 1
                logger.debug("Found header line at index %d, starting parse from index %d", i, start_idx)
                break
    
    for line in lines[start_idx:]:
        line = line.strip()
        if not line or not '|' in line:
            continue
        
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 7:
            logger.debug("Skipping line with %d parts (need at least 7): %s", len(parts), line[:100])
            continue
        
        try:
            # Format: Issue | No. | Patch | Category | Severity | Interactive | Status | Summary
            # (Note: "Since" column is not always present)
            # parts[0] = "cve" (Issue type)
            # parts[1] = "CVE-2025-7039" (CVE No.)
            # parts[2] = "openSUSE-SLE-15.6-2025-4308" (Patch)
            # parts[3] = "security" (Category)
            # parts[4] = "moderate" (Severity)
            # parts[5] = "---" (Interactive)
            # parts[6] = "needed" (Status)
            # parts[7] = "Security update for glib2" (Summary)
            
            issue_type = parts[0].strip() if len(parts) > 0 else ''
            cve_id = parts[1].strip() if len(parts) > 1 else ''
            patch_name = parts[2].strip() if len(parts) > 2 else ''
            category = parts[3].strip() if len(parts) > 3 else ''
            severity = parts[4].strip() if len(parts) > 4 else ''
            status = parts[6].strip() if len(parts) > 6 else ''
            # Summary is at parts[7] if no "Since" column, or parts[8] if "Since" exists
            # Try parts[7] first (most common case)
            description = parts[7].strip() if len(parts) > 7 else (parts[8].strip() if len(parts) > 8 else '')
            
            logger.debug("Parsed: issue_type=%s, cve_id=%s, patch=%s, category=%s, status=%s", 
                        issue_type, cve_id, patch_name, category, status)
            
            # Skip header line
            if issue_type.lower() == 'issue' or cve_id.lower() == 'no.':
                logger.debug("Skipping header line")
                continue
            
            # Only process security patches that are needed
            if category.lower() == 'security' and status.lower() == 'needed':
                logger.info("Found security patch: %s (CVE: %s)", patch_name, cve_id)
                patches.append({
                    'cve': cve_id,
                    'patch': patch_name,
                    'category': category,
                    'severity': severity,
                    'status': status,
                    'description': description,
                })
            else:
                logger.debug("Skipping patch (category=%s, status=%s): %s", category, status, patch_name)
        except (IndexError, ValueError) as e:
            logger.warning("Error parsing line: %s, error: %s", line[:100], e)
            continue
    
    logger.info("Parsed %d security patches from zypper list-patches --cve", len(patches))
    return patches


def _parse_zypper_lu_patch_security(output: str) -> List[Dict[str, Any]]:
    """
    Parse 'zypper lu -t patch' output and filter for security patches.
    
    Example output:
    # | Repository                          | Name                    | Version | Category    | Severity
    --+-------------------------------------+-------------------------+---------+-------------+----------
    1 | openSUSE-SLE-15.6-Updates           | openSUSE-SLE-15.6-2025-4308 | 1       | security    | moderate
    """
    patches = []
    lines = output.splitlines()
    
    # Find header separator line
    start_idx = 0
    for i, line in enumerate(lines):
        if '---' in line or '===' in line or ('|' in line and 'Category' in line):
            start_idx = i + 1
            break
    
    for line in lines[start_idx:]:
        line = line.strip()
        if not line or not '|' in line:
            continue
        
        # Skip lines that don't contain 'security'
        if 'security' not in line.lower():
            continue
        
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 4:
            continue
        
        try:
            # Format: Repository | Name | Category | Severity | Interactive | Status | Summary
            # (Note: "Since" column is not always present)
            # parts[0] = Repository name
            # parts[1] = Name (patch name)
            # parts[2] = Category
            # parts[3] = Severity
            # parts[4] = Interactive
            # parts[5] = Status
            # parts[6] = Summary (if no "Since"), or parts[7] if "Since" exists
            
            patch_name = parts[1].strip() if len(parts) > 1 else ''
            category = parts[2].strip() if len(parts) > 2 else ''
            severity = parts[3].strip() if len(parts) > 3 else ''
            # Summary is at parts[6] if no "Since" column, or parts[7] if "Since" exists
            description = parts[6].strip() if len(parts) > 6 else (parts[7].strip() if len(parts) > 7 else '')
            
            # Skip header line
            if patch_name.lower() == 'name' or category.lower() == 'category':
                continue
            
            # Only process security category
            if category.lower() == 'security':
                patches.append({
                    'cve': '',  # Will be filled from patch name or description if available
                    'patch': patch_name,
                    'category': category,
                    'severity': severity,
                    'status': 'needed',
                    'description': description if description else f'SUSE Security Advisory: {patch_name}',
                })
        except (IndexError, ValueError):
            continue
    
    return patches


def _get_patch_packages(patch_name: str) -> List[str]:
    """
    Get packages affected by a patch using 'zypper info -t patch <patch_name>'
    """
    try:
        completed = subprocess.run(
            ['zypper', 'info', '-t', 'patch', patch_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
            timeout=10,
        )
        
        if completed.returncode != 0:
            return []
        
        output = completed.stdout
        packages = []
        
        # Look for "Provides:" or "Requires:" lines that contain package names
        # Also look for package names in the description
        for line in output.splitlines():
            line = line.strip()
            # Extract package names from various formats
            # Example: "Provides: glib2 = 2.78.4-150600.3.1"
            if 'Provides:' in line or 'Requires:' in line:
                # Extract package name (before = or space)
                match = re.search(r'(\S+)\s*[=<>]', line)
                if match:
                    pkg_name = match.group(1)
                    if pkg_name and pkg_name not in packages:
                        packages.append(pkg_name)
            
            # Also check for package names in "Information" or "Summary" sections
            # Example: "Security update for glib2"
            if 'for ' in line.lower() and ('security' in line.lower() or 'update' in line.lower()):
                # Try to extract package name after "for"
                match = re.search(r'for\s+(\S+)', line, re.IGNORECASE)
                if match:
                    pkg_name = match.group(1)
                    # Filter out common words
                    if pkg_name and pkg_name not in ['the', 'a', 'an', 'this', 'that'] and pkg_name not in packages:
                        packages.append(pkg_name)
        
        return packages
    except Exception:
        return []


def _get_cves_from_patches(patches: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Convert patches to CVE format grouped by package.
    Returns: {package_name: [cve_info, ...]}
    """
    package_cves: Dict[str, List[Dict[str, Any]]] = {}
    
    for patch in patches:
        patch_name = patch.get('patch', '')
        cve_id = patch.get('cve', '').strip()
        severity = patch.get('severity', '')
        description = patch.get('description', '')
        
        # Get packages affected by this patch
        affected_packages = _get_patch_packages(patch_name)
        
        # If no packages found from zypper info, try to extract from patch name
        # Some patches have package names in their description
        if not affected_packages:
            # Try to extract package name from description
            # Example: "Security update for glib2" -> glib2
            desc_lower = description.lower()
            if 'for ' in desc_lower:
                parts = desc_lower.split('for ')
                if len(parts) > 1:
                    potential_pkg = parts[-1].split()[0].strip()
                    if potential_pkg:
                        affected_packages = [potential_pkg]
        
        # If still no packages, use patch name as fallback
        if not affected_packages:
            # Extract potential package name from patch name
            # Example: "openSUSE-SLE-15.6-2025-4308" -> try to find package in description
            continue  # Skip patches without identifiable packages
        
        # Create CVE entry
        # If no CVE ID, use SUSE advisory format (patch name or generic)
        if not cve_id or not cve_id.startswith('CVE-'):
            # Try to extract CVE from description if available
            cve_match = re.search(r'CVE-\d{4}-\d{4,}', description, re.IGNORECASE)
            if cve_match:
                cve_id = cve_match.group(0)
            else:
                # Use patch name as advisory identifier
                cve_id = f'SUSE-{patch_name}'
        
        cve_entry = {
            'cve': cve_id,
            'patch': patch_name,
            'severity': severity,
            'description': description if description else f'SUSE Security Advisory: {patch_name}',
            'status': 'open',  # All patches from zypper are "needed" = open
        }
        
        # Add to each affected package
        for pkg_name in affected_packages:
            if pkg_name not in package_cves:
                package_cves[pkg_name] = []
            package_cves[pkg_name].append(cve_entry)
    
    return package_cves


def _scan_with_zypper_methods() -> Dict[str, List[Dict[str, Any]]]:
    """
    Use both zypper methods to get CVE information.
    Method 1: zypper list-patches --cve (preferred, has CVE IDs)
    Method 2: zypper lu -t patch | grep security (fallback, may not have CVE IDs)
    
    Returns: {package_name: [cve_info, ...]}
    """
    all_package_cves: Dict[str, List[Dict[str, Any]]] = {}
    
    # Method 1: zypper list-patches --cve
    try:
        completed = subprocess.run(
            ['zypper', 'list-patches', '--cve'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
            timeout=30,
        )
        
        if completed.returncode == 0:
            patches = _parse_zypper_list_patches_cve(completed.stdout)
            method1_cves = _get_cves_from_patches(patches)
            
            # Merge into all_package_cves
            for pkg_name, cves in method1_cves.items():
                if pkg_name not in all_package_cves:
                    all_package_cves[pkg_name] = []
                # Avoid duplicates
                existing_cves = {c.get('cve', '') for c in all_package_cves[pkg_name]}
                for cve in cves:
                    if cve.get('cve', '') not in existing_cves:
                        all_package_cves[pkg_name].append(cve)
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        # zypper not available or command failed
        pass
    except Exception:
        # Other errors - continue to method 2
        pass
    
    # Method 2: zypper lu -t patch (filter for security)
    try:
        completed = subprocess.run(
            ['zypper', 'lu', '-t', 'patch'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
            timeout=30,
        )
        
        if completed.returncode == 0:
            patches = _parse_zypper_lu_patch_security(completed.stdout)
            method2_cves = _get_cves_from_patches(patches)
            
            # Merge into all_package_cves (avoid duplicates)
            for pkg_name, cves in method2_cves.items():
                if pkg_name not in all_package_cves:
                    all_package_cves[pkg_name] = []
                existing_cves = {c.get('cve', '') for c in all_package_cves[pkg_name]}
                for cve in cves:
                    if cve.get('cve', '') not in existing_cves:
                        all_package_cves[pkg_name].append(cve)
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        # zypper not available or command failed
        pass
    except Exception:
        # Other errors
        pass
    
    return all_package_cves


def process_batch(packages: List[Dict[str, str]], batch_num: int, total_batches: int) -> Dict[str, Any]:
    """Process a batch of packages by matching against zypper CVE data"""
    ensure_cache_dir()
    
    batch_results = {
        'batch_number': batch_num,
        'total_packages': len(packages),
        'packages_with_cves': 0,
        'total_cves': 0,
        'timestamp': datetime.utcnow().isoformat(),
        'results': []
    }
    
    # Get all CVE data from zypper (once per batch, not per package)
    # This is more efficient than calling zypper for each package
    package_cves_map = _scan_with_zypper_methods()
    
    # Match packages with CVEs
    for package in packages:
        package_name = package['name']
        package_version = package['version']
        
        # Find CVEs for this package (case-insensitive match)
        package_cves = []
        for pkg_name, cves in package_cves_map.items():
            if pkg_name.lower() == package_name.lower():
                package_cves.extend(cves)
        
        if not package_cves:
            continue
        
        # Format CVE data for this package
        formatted_cves = []
        for cve_info in package_cves:
            cve_id = cve_info.get('cve', '')
            # If no CVE ID, use SUSE advisory format
            if not cve_id or not cve_id.startswith('CVE-'):
                cve_id = cve_info.get('patch', 'SUSE-Security-Advisory')
            
            formatted_cves.append({
                'advisory': cve_id,
                'package': package_name,
                'installed_version': package_version,
                'affected': package_version,  # We don't have exact affected version from zypper
                'fixed': '',  # zypper doesn't provide fixed version directly
                'issues': [cve_id] if cve_id.startswith('CVE-') else [],
                'severity': cve_info.get('severity', 'unknown'),
                'status': 'open',  # All patches from zypper are "needed" = open
                'description': cve_info.get('description', ''),
                'patch': cve_info.get('patch', ''),
                'source': 'SUSE Security Advisory'
            })
        
        if formatted_cves:
            batch_results['packages_with_cves'] += 1
            batch_results['total_cves'] += len(formatted_cves)
            batch_results['results'].append({
                'package': package_name,
                'version': package_version,
                'matches': formatted_cves,
                'cve_count': len(formatted_cves)
            })
    
    # Save batch result to JSON file
    batch_json_path = os.path.join(BATCH_RESULTS_DIR, f"batch_{batch_num}.json")
    try:
        with open(batch_json_path, "w", encoding="utf-8") as f:
            json.dump(batch_results, f, ensure_ascii=False, indent=2)
    except PermissionError:
        pass
    
    return batch_results


def scan_cves(packages: List[Dict[str, str]], batch_size: int = BATCH_SIZE) -> List[Dict[str, Any]]:
    """Scan CVEs for all packages in batches"""
    total_packages = len(packages)
    total_batches = (total_packages + batch_size - 1) // batch_size
    
    # Clean up old batch result files before starting new scan
    ensure_cache_dir()
    try:
        if os.path.exists(BATCH_RESULTS_DIR):
            for filename in os.listdir(BATCH_RESULTS_DIR):
                if filename.startswith("batch_") and filename.endswith(".json"):
                    file_path = os.path.join(BATCH_RESULTS_DIR, filename)
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
    except Exception:
        pass
    
    all_results = []
    
    # Process packages in batches
    for i in range(0, total_packages, batch_size):
        batch_num = (i // batch_size) + 1
        batch = packages[i:i + batch_size]
        
        batch_result = process_batch(batch, batch_num, total_batches)
        all_results.append(batch_result)
    
    return all_results


def match_advisories(
    installed_packages: List[Dict[str, str]], batch_results: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], int]:
    """Convert batch results to matched format"""
    matches: List[Dict[str, Any]] = []
    
    for batch_result in batch_results:
        for pkg_result in batch_result.get('results', []):
            matches_list = pkg_result.get('matches', [])
            matches.extend(matches_list)
    
    ensure_cache_dir()
    try:
        with open(MATCHED_PATH, "w", encoding="utf-8") as f:
            json.dump({"matched": matches, "timestamp": datetime.utcnow().isoformat()}, f, ensure_ascii=False)
    except PermissionError:
        pass
    
    return matches, len(matches)


def run_scan(force_refresh: bool = False, use_system: bool = True, 
            batch_size: int = BATCH_SIZE) -> Dict[str, Any]:
    """Main scan function that gets packages and checks for CVEs"""
    installed = get_installed_packages(use_system=use_system)
    
    if not installed:
        return {
            "total_installed": 0,
            "total_advisories": 0,
            "total_matched": 0,
            "matched": [],
        }
    
    # Scan CVEs in batches
    batch_results = scan_cves(installed, batch_size=batch_size)
    
    # Convert to matched format
    matched, total = match_advisories(installed, batch_results)
    
    # Calculate total advisories (unique CVE/advisory names)
    unique_advisories = set()
    for batch_result in batch_results:
        for pkg_result in batch_result.get('results', []):
            for match in pkg_result.get('matches', []):
                advisory_name = match.get('advisory', '')
                if advisory_name:
                    unique_advisories.add(advisory_name)
    
    return {
        "total_installed": len(installed),
        "total_advisories": len(unique_advisories),
        "total_matched": total,
        "matched": matched,
    }

