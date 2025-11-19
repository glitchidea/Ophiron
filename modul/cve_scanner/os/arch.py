import json
import os
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple

import requests


CVE_API_URL = "https://security.archlinux.org/issues/all.json"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
CACHE_DIR = os.path.join(BASE_DIR, "cache", "arch")
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
        CACHE_DIR = os.path.join(os.path.expanduser("~"), ".ophiron_cache", "arch")
        INSTALLED_PATH = os.path.join(CACHE_DIR, "installed.json")
        MATCHED_PATH = os.path.join(CACHE_DIR, "matched.json")
        BATCH_RESULTS_DIR = os.path.join(CACHE_DIR, "batch_results")
        os.makedirs(CACHE_DIR, exist_ok=True)
        os.makedirs(BATCH_RESULTS_DIR, exist_ok=True)


def query_cves_for_packages_batch(package_names: List[str], all_advisories: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Filter advisories for a batch of packages from all_advisories"""
    result: Dict[str, List[Dict[str, Any]]] = {}
    package_set = {p.lower(): p for p in package_names}
    
    for advisory in all_advisories:
        adv_packages = advisory.get("packages", [])
        if not adv_packages:
            continue
        
        # Check if any of our packages match
        for adv_pkg in adv_packages:
            adv_pkg_lower = adv_pkg.lower()
            if adv_pkg_lower in package_set:
                pkg_name = package_set[adv_pkg_lower]
                if pkg_name not in result:
                    result[pkg_name] = []
                result[pkg_name].append(advisory)
                break
    
    return result


def get_all_advisories_once() -> List[Dict[str, Any]]:
    """Get all advisories from Arch Linux Security API once (no caching to disk)"""
    try:
        response = requests.get(CVE_API_URL, timeout=60)
        response.raise_for_status()
        all_advisories = response.json()
        
        if not isinstance(all_advisories, list):
            return []
        
        return all_advisories
    
    except requests.exceptions.RequestException:
        return []
    except json.JSONDecodeError:
        return []
    except Exception:
        return []


def _parse_pacman_q_output(output: str) -> List[Dict[str, str]]:
    packages: List[Dict[str, str]] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        # pacman -Q prints: name version
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        name, version = parts
        packages.append({"name": name, "version": version})
    return packages


def get_installed_packages(use_system: bool = True) -> List[Dict[str, str]]:
    ensure_cache_dir()
    if use_system:
        try:
            completed = subprocess.run(
                ["pacman", "-Q"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
            packages = _parse_pacman_q_output(completed.stdout)
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


def process_batch(packages: List[Dict[str, str]], batch_num: int, total_batches: int, 
                 all_advisories: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process a batch of 400 packages, query CVEs and save result to JSON"""
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
    
    # Query CVEs for this batch (400 packages at once)
    cve_map = query_cves_for_packages_batch(package_names, all_advisories)
    
    # Process each package in the batch
    for package in packages:
        package_name = package['name']
        package_version = package['version']
        advisories = cve_map.get(package_name, [])
        
        if not advisories:
            continue
        
        package_matches = []
        for adv in advisories:
            try:
                affected_version = adv.get("affected")
                issues = adv.get("issues", [])
                name = adv.get("name")
                severity = adv.get("severity")
                status = adv.get("status")
                fixed = adv.get("fixed")

                if not affected_version:
                    continue

                vulnerable = False
                # Rule 1: exact affected match (strict)
                if package_version == affected_version:
                    vulnerable = True
                # Rule 2: if fixed exists and installed < fixed (still vulnerable)
                elif fixed:
                    try:
                        # Prefer pacman's vercmp for accurate Arch version semantics
                        cmp_proc = subprocess.run(
                            ["vercmp", package_version, fixed],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            check=False,
                        )
                        # vercmp returns -1, 0, 1 on stdout
                        out = (cmp_proc.stdout or "").strip()
                        if out == "-1":
                            vulnerable = True
                    except Exception:
                        # Fallback: naive comparison (may be inaccurate for some arch versions)
                        vulnerable = package_version < fixed
                # Rule 3: if NO fixed but affected exists → installed <= affected → vulnerable
                elif affected_version:
                    try:
                        cmp_proc = subprocess.run(
                            ["vercmp", package_version, affected_version],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            check=False,
                        )
                        out = (cmp_proc.stdout or "").strip()
                        if out in ("-1", "0"):
                            vulnerable = True
                    except Exception:
                        # Fallback: naive comparison
                        if package_version <= affected_version:
                            vulnerable = True

                if vulnerable:
                    package_matches.append({
                        "advisory": name,
                        "package": package_name,
                        "installed_version": package_version,
                        "affected": affected_version,
                        "fixed": fixed,
                        "issues": issues,
                        "severity": severity,
                        "status": status,
                    })
            except Exception:
                continue
        
        if package_matches:
            batch_results['packages_with_cves'] += 1
            batch_results['total_cves'] += len(package_matches)
            batch_results['results'].append({
                'package': package_name,
                'version': package_version,
                'matches': package_matches,
                'match_count': len(package_matches)
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
    
    # Get all advisories once (needed to filter for each batch)
    all_advisories = get_all_advisories_once()
    
    if not all_advisories:
        return []
    
    all_results = []
    
    # Process packages in batches of 400, each batch queries and saves to JSON
    for i in range(0, total_packages, batch_size):
        batch_num = (i // batch_size) + 1
        batch = packages[i:i + batch_size]
        
        # Query CVEs for this batch (400 packages) and save to JSON
        batch_result = process_batch(batch, batch_num, total_batches, all_advisories)
        all_results.append(batch_result)
        
        # Small delay between batches
        if i + batch_size < total_packages:
            time.sleep(0.5)
    
    return all_results


def match_advisories(
    installed_packages: List[Dict[str, str]], batch_results: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], int]:
    """Convert batch results to matched format"""
    matches: List[Dict[str, Any]] = []
    
    for batch_result in batch_results:
        for pkg_result in batch_result.get('results', []):
            package_matches = pkg_result.get('matches', [])
            matches.extend(package_matches)
    
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
    # Each batch queries and saves result to JSON file
    batch_results = scan_cves(installed, batch_size=batch_size)
    
    # Convert to matched format
    matched, total = match_advisories(installed, batch_results)
    
    # Calculate total advisories (unique CVE names)
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

