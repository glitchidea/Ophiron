import json
import os
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple

import requests


DEBIAN_TRACKER_URL = "https://security-tracker.debian.org/tracker/data/json"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
CACHE_DIR = os.path.join(BASE_DIR, "cache", "debian")
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
        CACHE_DIR = os.path.join(os.path.expanduser("~"), ".ophiron_cache", "debian")
        INSTALLED_PATH = os.path.join(CACHE_DIR, "installed.json")
        MATCHED_PATH = os.path.join(CACHE_DIR, "matched.json")
        BATCH_RESULTS_DIR = os.path.join(CACHE_DIR, "batch_results")
        os.makedirs(CACHE_DIR, exist_ok=True)
        os.makedirs(BATCH_RESULTS_DIR, exist_ok=True)


def get_tracker_data_once() -> Dict[str, Any]:
    """Get Debian Security Tracker JSON once (no caching to disk)"""
    try:
        response = requests.get(DEBIAN_TRACKER_URL, timeout=120)
        response.raise_for_status()
        tracker_data = response.json()
        
        if not isinstance(tracker_data, dict):
            return {}
        
        return tracker_data
    
    except requests.exceptions.RequestException:
        return {}
    except json.JSONDecodeError:
        return {}
    except Exception:
        return {}


def find_cves_for_package(package_name: str, package_version: str, tracker_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Find CVEs for a package in Debian Security Tracker data"""
    if package_name not in tracker_data:
        return []
    
    package_data = tracker_data[package_name]
    cves = []
    seen_cves = set()
    
    for cve_id, cve_data in package_data.items():
        if not cve_id.startswith('CVE-'):
            continue
        
        if cve_id in seen_cves:
            continue
        
        # Check releases for this CVE
        releases = cve_data.get('releases', {})
        
        if not releases:
            continue
        
        # Check all releases for matching version or open status
        for release_name, release_data in releases.items():
            if not isinstance(release_data, dict):
                continue
            
            status = release_data.get('status', 'unknown')
            repositories = release_data.get('repositories', {})
            
            # Check if package version matches any repository version
            version_matched = False
            if isinstance(repositories, dict):
                for repo_name, repo_version in repositories.items():
                    if repo_version == package_version:
                        version_matched = True
                        break
            
            # Add CVE if version matches or status is open
            if version_matched or status == 'open':
                fixed_version = release_data.get('fixed_version', '')
                urgency = release_data.get('urgency', 'unknown')
                
                cves.append({
                    'CVE': cve_id,
                    'status': status,
                    'severity': urgency,
                    'description': cve_data.get('description', ''),
                    'scope': cve_data.get('scope', ''),
                    'fixed_version': fixed_version,
                    'release': release_name,
                    'repositories': repositories,
                    'debianbug': cve_data.get('debianbug', '')
                })
                seen_cves.add(cve_id)
                break
    
    return cves


def query_cves_for_packages_batch(package_names: List[str], package_versions: Dict[str, str], 
                                  tracker_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Query CVEs for a batch of packages from tracker data"""
    result: Dict[str, List[Dict[str, Any]]] = {}
    
    for package_name in package_names:
        package_version = package_versions.get(package_name, '')
        if package_version:
            cves = find_cves_for_package(package_name, package_version, tracker_data)
            if cves:
                result[package_name] = cves
    
    return result


def _parse_dpkg_output(output: str) -> List[Dict[str, str]]:
    """Parse dpkg -l output into list of packages with name and version"""
    packages: List[Dict[str, str]] = []
    for line in output.splitlines():
        line = line.strip()
        # Skip header lines - only process lines starting with 'ii '
        if not line.startswith('ii '):
            continue
        
        parts = line.split()
        if len(parts) >= 3:
            name = parts[1]
            version = parts[2]
            
            # Skip packages with no version
            if version == '<none>':
                continue
            
            packages.append({"name": name, "version": version})
    
    return packages


def get_installed_packages(use_system: bool = True) -> List[Dict[str, str]]:
    """Get all installed packages using dpkg command"""
    ensure_cache_dir()
    if use_system:
        try:
            completed = subprocess.run(
                ['dpkg', '-l'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
            packages = _parse_dpkg_output(completed.stdout)
            payload = {"packages": packages, "timestamp": datetime.utcnow().isoformat()}
            try:
                with open(INSTALLED_PATH, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False)
            except PermissionError:
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
                 tracker_data: Dict[str, Any]) -> Dict[str, Any]:
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
    package_versions = {pkg['name']: pkg['version'] for pkg in packages}
    
    # Query CVEs for this batch (400 packages at once)
    cve_map = query_cves_for_packages_batch(package_names, package_versions, tracker_data)
    
    # Process each package in the batch
    for package in packages:
        package_name = package['name']
        package_version = package['version']
        cves = cve_map.get(package_name, [])
        
        if not cves:
            continue
        
        # Format CVE data for matched format
        package_matches = []
        for cve in cves:
            package_matches.append({
                "advisory": cve.get('CVE', ''),
                "package": package_name,
                "installed_version": package_version,
                "affected": package_version,  # Debian tracker doesn't provide exact affected version
                "fixed": cve.get('fixed_version', ''),
                "issues": [cve.get('CVE', '')],
                "severity": cve.get('severity', ''),
                "status": cve.get('status', ''),
                "description": cve.get('description', ''),
                "scope": cve.get('scope', ''),
                "release": cve.get('release', ''),
                "debianbug": cve.get('debianbug', ''),
            })
        
        if package_matches:
            batch_results['packages_with_cves'] += 1
            batch_results['total_cves'] += len(package_matches)
            batch_results['results'].append({
                'package': package_name,
                'version': package_version,
                'matches': package_matches,
                'cve_count': len(package_matches)
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
    
    # Get tracker data once (no caching to disk, just in memory for this scan)
    tracker_data = get_tracker_data_once()
    
    if not tracker_data:
        return []
    
    all_results = []
    
    # Process packages in batches of 400, each batch queries and saves to JSON
    for i in range(0, total_packages, batch_size):
        batch_num = (i // batch_size) + 1
        batch = packages[i:i + batch_size]
        
        # Query CVEs for this batch (400 packages) and save to JSON
        batch_result = process_batch(batch, batch_num, total_batches, tracker_data)
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

