import json
import os
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

import requests


UBUNTU_CVES_URL = "https://ubuntu.com/security/cves.json"
UBUNTU_NOTICES_URL = "https://ubuntu.com/security/notices.json"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
CACHE_DIR = os.path.join(BASE_DIR, "cache", "ubuntu")
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
        CACHE_DIR = os.path.join(os.path.expanduser("~"), ".ophiron_cache", "ubuntu")
        INSTALLED_PATH = os.path.join(CACHE_DIR, "installed.json")
        MATCHED_PATH = os.path.join(CACHE_DIR, "matched.json")
        BATCH_RESULTS_DIR = os.path.join(CACHE_DIR, "batch_results")
        os.makedirs(CACHE_DIR, exist_ok=True)
        os.makedirs(BATCH_RESULTS_DIR, exist_ok=True)


def get_security_data_once() -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    Download Ubuntu security JSON files once (for a batch) and return them
    Returns tuple of (cves_data, notices_data) or None on error
    """
    try:
        # Download CVEs JSON
        response_cves = requests.get(UBUNTU_CVES_URL, timeout=120)
        response_cves.raise_for_status()
        cves_data = response_cves.json()
        
        # Download Notices JSON
        response_notices = requests.get(UBUNTU_NOTICES_URL, timeout=120)
        response_notices.raise_for_status()
        notices_data = response_notices.json()
        
        return (cves_data, notices_data)
    
    except requests.exceptions.RequestException:
        return None
    except json.JSONDecodeError:
        return None
    except Exception:
        return None


def find_cves_for_package(package_name: str, package_version: str, 
                          cves_data: Dict[str, Any], notices_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Find CVEs for a package in Ubuntu security data
    
    Ubuntu JSON formatı:
    - CVEs: {"cves": [{"id": "CVE-...", "packages": [{"name": "...", "statuses": [...]}]}]}
    - Notices: {"notices": [{"id": "USN-...", "cves": [...], "release_packages": {...}}]}
    """
    cves = []
    seen_cves = set()
    
    # CVEs JSON'dan CVE'leri bul
    # Format: {"cves": [{"id": "CVE-...", "packages": [{"name": "pkg", "statuses": [...]}]}]}
    if isinstance(cves_data, dict) and 'cves' in cves_data:
        cves_list = cves_data.get('cves', [])
        
        for cve_info in cves_list:
            if not isinstance(cve_info, dict):
                continue
            
            cve_id = cve_info.get('id', '')
            if not cve_id.startswith('CVE-') or cve_id in seen_cves:
                continue
            
            # Packages bir liste olarak geliyor
            packages_list = cve_info.get('packages', [])
            if not isinstance(packages_list, list):
                continue
            
            # Paket listesinde arama yap
            for pkg_info in packages_list:
                if not isinstance(pkg_info, dict):
                    continue
                
                pkg_name = pkg_info.get('name', '')
                if pkg_name != package_name:
                    continue
                
                # Statuses listesini kontrol et
                statuses = pkg_info.get('statuses', [])
                if not isinstance(statuses, list):
                    continue
                
                for status_info in statuses:
                    if not isinstance(status_info, dict):
                        continue
                    
                    release = status_info.get('release_codename', '')
                    status = status_info.get('status', '')
                    pocket = status_info.get('pocket', '')
                    
                    # Eğer "not-affected" değilse CVE var
                    if status and status.lower() not in ['not-affected', 'not_affected']:
                        cves.append({
                            'CVE': cve_id,
                            'status': status,
                            'description': cve_info.get('description', ''),
                            'priority': cve_info.get('priority', 'unknown'),
                            'package': package_name,
                            'release': release,
                            'pocket': pocket,
                            'source': 'cves.json'
                        })
                        seen_cves.add(cve_id)
                        break  # Bu CVE için bir kez ekle, release'leri tek tek ekleme
                break  # Paket bulundu, başka CVE'lere geç
    
    # Notices JSON'dan CVE'leri bul
    # Format: {"notices": [{"id": "USN-...", "cves": [{"id": "CVE-..."}], "release_packages": {"release": [pkg_list]}}]}
    if isinstance(notices_data, dict) and 'notices' in notices_data:
        notices_list = notices_data.get('notices', [])
        
        for notice_info in notices_list:
            if not isinstance(notice_info, dict):
                continue
            
            notice_id = notice_info.get('id', '')
            
            # Release packages yapısını kontrol et
            release_packages = notice_info.get('release_packages', {})
            if not isinstance(release_packages, dict):
                continue
            
            # Her release için paketleri kontrol et
            package_found_releases = []
            for release, pkg_list in release_packages.items():
                if not isinstance(pkg_list, list):
                    continue
                
                # Paket listesinde arama
                for pkg in pkg_list:
                    if isinstance(pkg, dict):
                        pkg_name = pkg.get('name', '') or pkg.get('package_name', '')
                    elif isinstance(pkg, str):
                        pkg_name = pkg
                    else:
                        continue
                    
                    if pkg_name == package_name:
                        package_found_releases.append(release)
                        break
            
            # Paket bulunduysa, notice'daki CVE'leri ekle
            if package_found_releases:
                cves_list = notice_info.get('cves', [])
                if isinstance(cves_list, list):
                    for cve_item in cves_list:
                        if isinstance(cve_item, dict):
                            cve_id = cve_item.get('id', '')
                        elif isinstance(cve_item, str):
                            cve_id = cve_item
                        else:
                            continue
                        
                        if cve_id.startswith('CVE-') and cve_id not in seen_cves:
                            # Tüm release'ler için ekle
                            for release in package_found_releases:
                                cves.append({
                                    'CVE': cve_id,
                                    'status': notice_info.get('type', 'unknown'),
                                    'description': notice_info.get('summary', notice_info.get('description', '')),
                                    'priority': 'unknown',  # Notices'da priority genelde yok
                                    'package': package_name,
                                    'release': release,
                                    'notice': notice_id,
                                    'source': 'notices.json'
                                })
                            seen_cves.add(cve_id)
    
    return cves


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
                 cves_data: Dict[str, Any], notices_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a batch of 400 packages:
    1. JSON'ları geçici olarak indir (hafızada)
    2. 400 paketi tek seferde işle (sıralı, toplu)
    3. Sonuçları JSON'a kaydet
    """
    ensure_cache_dir()
    
    batch_results = {
        'batch_number': batch_num,
        'total_packages': len(packages),
        'packages_with_cves': 0,
        'total_cves': 0,
        'timestamp': datetime.utcnow().isoformat(),
        'results': []
    }
    
    # 400 paketi tek seferde, sıralı olarak işle
    for pkg in packages:
        cves = find_cves_for_package(pkg['name'], pkg['version'], cves_data, notices_data)
        
        if cves:
            # Format CVE data for matched format
            package_matches = []
            for cve in cves:
                package_matches.append({
                    "advisory": cve.get('CVE', ''),
                    "package": pkg['name'],
                    "installed_version": pkg['version'],
                    "affected": pkg['version'],
                    "fixed": "",
                    "issues": [cve.get('CVE', '')],
                    "severity": cve.get('priority', ''),
                    "status": cve.get('status', ''),
                    "description": cve.get('description', ''),
                    "release": cve.get('release', ''),
                    "pocket": cve.get('pocket', ''),
                    "notice": cve.get('notice', ''),
                    "source": cve.get('source', '')
                })
            
            batch_results['packages_with_cves'] += 1
            batch_results['total_cves'] += len(package_matches)
            batch_results['results'].append({
                'package': pkg['name'],
                'version': pkg['version'],
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
    """
    Scan CVEs for all packages in batches of 400
    Her batch için:
    - JSON'ları geçici olarak indir (hafızada) - TEK SEFERDE
    - 400 paketi tek seferde işle (sıralı, toplu)
    - Sonuçları JSON'a kaydet
    """
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
    
    # Process packages in batches of 400
    for i in range(0, total_packages, batch_size):
        batch_num = (i // batch_size) + 1
        batch = packages[i:i + batch_size]
        
        # Her batch için JSON'ları geçici olarak indir (hafızada) - TEK SEFERDE
        result = get_security_data_once()
        if result is None:
            # JSON'lar indirilemedi, boş batch result ekle
            batch_results = {
                'batch_number': batch_num,
                'total_packages': len(batch),
                'packages_with_cves': 0,
                'total_cves': 0,
                'timestamp': datetime.utcnow().isoformat(),
                'results': []
            }
            all_results.append(batch_results)
            continue
        
        cves_data, notices_data = result
        
        # 400 paketi tek seferde işle (sıralı, toplu)
        batch_result = process_batch(batch, batch_num, total_batches, cves_data, notices_data)
        all_results.append(batch_result)
        
        # JSON'ları hafızadan temizle (garbage collection için)
        del cves_data
        del notices_data
        
        # Batch'ler arasında kısa bir bekleme (rate limiting için)
        if i + batch_size < total_packages:
            time.sleep(1)  # Rate limiting için 1 saniye bekle
    
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
    # Each batch downloads JSONs temporarily, processes 400 packages, and saves result to JSON file
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

