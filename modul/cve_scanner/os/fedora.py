import json
import os
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple

import requests


CVE_API_URL = "https://access.redhat.com/hydra/rest/securitydata/cve.json"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
CACHE_DIR = os.path.join(BASE_DIR, "cache", "fedora")
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
        CACHE_DIR = os.path.join(os.path.expanduser("~"), ".ophiron_cache", "fedora")
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
    """Get all installed packages using rpm command"""
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


def query_cves_for_packages_batch(package_names: List[str], timeout: int = 30) -> Dict[str, List[Dict[str, Any]]]:
    """Query Red Hat CVE API for multiple packages in a single request"""
    result: Dict[str, List[Dict[str, Any]]] = {}
    
    if not package_names:
        return result
    
    try:
        # Red Hat API supports multiple 'package' parameters in a single request
        # We can send all package names in one query
        params = [('package', pkg_name) for pkg_name in package_names]
        response = requests.get(CVE_API_URL, params=params, timeout=timeout)
        response.raise_for_status()
        
        data = response.json()
        if not isinstance(data, list):
            return result
        
        # Group CVEs by package name
        for cve_entry in data:
            affected_packages = cve_entry.get('affected_packages', [])
            if not affected_packages:
                continue
            
            # Find which of our packages match this CVE
            for package_name in package_names:
                package_name_lower = package_name.lower()
                for affected_pkg in affected_packages:
                    if package_name_lower in affected_pkg.lower():
                        if package_name not in result:
                            result[package_name] = []
                        result[package_name].append(cve_entry)
                        break
        
        return result
    
    except requests.exceptions.RequestException:
        # API errors - return empty dict
        return {}
    except json.JSONDecodeError:
        # JSON parse errors - return empty dict
        return {}
    except Exception:
        # Other errors - return empty dict
        return {}


def process_batch(packages: List[Dict[str, str]], batch_num: int, total_batches: int) -> Dict[str, Any]:
    """Process a batch of 400 packages with a single API query"""
    ensure_cache_dir()
    
    batch_results = {
        'batch_number': batch_num,
        'total_packages': len(packages),
        'packages_with_cves': 0,
        'total_cves': 0,
        'timestamp': datetime.utcnow().isoformat(),
        'results': []
    }
    
    package_names = [pkg['name'] for pkg in packages]
    
    # Single API query for all 400 packages
    cve_map = query_cves_for_packages_batch(package_names)
    
    # Process results for each package
    for package in packages:
        package_name = package['name']
        package_version = package['version']
        cves = cve_map.get(package_name, [])
        
        if not cves:
            continue
        
        # Format CVE data
        package_cves = []
        for cve in cves:
            package_cves.append({
                'CVE': cve.get('CVE', ''),
                'severity': cve.get('severity', ''),
                'public_date': cve.get('public_date', ''),
                'description': cve.get('bugzilla_description', ''),
                'affected_packages': cve.get('affected_packages', []),
                'resource': cve.get('resource_url', '')
            })
        
        if package_cves:
            batch_results['packages_with_cves'] += 1
            batch_results['total_cves'] += len(package_cves)
            batch_results['results'].append({
                'package': package_name,
                'version': package_version,
                'cves': package_cves,
                'cve_count': len(package_cves)
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
    """Scan CVEs for all packages in batches of 400, save each batch result to JSON"""
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
    
    # Process packages in batches of 400, each batch makes a single API query
    for i in range(0, total_packages, batch_size):
        batch_num = (i // batch_size) + 1
        batch = packages[i:i + batch_size]
        
        # Single API query for this batch (400 packages)
        batch_result = process_batch(batch, batch_num, total_batches)
        all_results.append(batch_result)
        
        # Small delay between batches
        if i + batch_size < total_packages:
            time.sleep(0.5)
    
    return all_results


def match_advisories(
    installed_packages: List[Dict[str, str]], batch_results: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], int]:
    """Convert batch results to matched format similar to Arch"""
    matches: List[Dict[str, Any]] = []
    
    for batch_result in batch_results:
        for pkg_result in batch_result.get('results', []):
            package_name = pkg_result.get('package')
            package_version = pkg_result.get('version')
            cves = pkg_result.get('cves', [])
            
            for cve_info in cves:
                matches.append({
                    'advisory': cve_info.get('CVE', ''),
                    'package': package_name,
                    'installed_version': package_version,
                    'affected': '',  # Red Hat API doesn't provide exact affected version in this format
                    'fixed': '',  # Red Hat API doesn't provide fixed version in this format
                    'issues': [cve_info.get('CVE', '')],
                    'severity': cve_info.get('severity', ''),
                    'status': '',  # Red Hat API doesn't provide status
                    'description': cve_info.get('description', ''),
                    'public_date': cve_info.get('public_date', ''),
                    'affected_packages': cve_info.get('affected_packages', []),
                    'resource': cve_info.get('resource', '')
                })
    
    ensure_cache_dir()
    try:
        with open(MATCHED_PATH, "w", encoding="utf-8") as f:
            json.dump({"matched": matches, "timestamp": datetime.utcnow().isoformat()}, f, ensure_ascii=False)
    except PermissionError:
        # If we can't write to the matched file, just continue without caching
        pass
    
    return matches, len(matches)


def run_scan(force_refresh: bool = False, use_system: bool = True, 
            batch_size: int = BATCH_SIZE) -> Dict[str, Any]:
    """Main scan function that gets packages and checks for CVEs in batches of 400"""
    installed = get_installed_packages(use_system=use_system)
    
    if not installed:
        return {
            "total_installed": 0,
            "total_advisories": 0,
            "total_matched": 0,
            "matched": [],
        }
    
    # Scan CVEs in batches (400 packages at a time)
    # Each batch makes a single API query for all 400 packages
    batch_results = scan_cves(installed, batch_size=batch_size)
    
    # Convert to matched format
    matched, total = match_advisories(installed, batch_results)
    
    # Calculate total advisories (unique CVEs)
    unique_cves = set()
    for batch_result in batch_results:
        for pkg_result in batch_result.get('results', []):
            for cve_info in pkg_result.get('cves', []):
                unique_cves.add(cve_info.get('CVE', ''))
    
    return {
        "total_installed": len(installed),
        "total_advisories": len(unique_cves),
        "total_matched": total,
        "matched": matched,
    }

