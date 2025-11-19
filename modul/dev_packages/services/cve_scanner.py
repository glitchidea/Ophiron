"""
CVE Scanner service using OSV.dev API
Supports batch queries with rate limiting (50 packages per request)
"""
import json
import re
import time
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
from django.core.cache import cache


# OSV.dev API endpoint
OSV_API_BASE = "https://api.osv.dev/v1"
OSV_BATCH_ENDPOINT = f"{OSV_API_BASE}/querybatch"

# Batch size for rate limiting
BATCH_SIZE = 50

# Cache timeout (1 hour)
CACHE_TIMEOUT = 3600


# Package manager to OSV ecosystem mapping
ECOSYSTEM_MAP = {
    'pip': 'PyPI',
    'npm': 'npm',
    'gem': 'RubyGems',
    'composer': 'Packagist',
    'cargo': 'crates.io',
    'go': 'Go',
    'dotnet': 'NuGet',
}


def get_ecosystem(manager: str) -> Optional[str]:
    """Get OSV ecosystem name for a package manager"""
    return ECOSYSTEM_MAP.get(manager)


def normalize_version(version: str) -> str:
    """
    Normalize version string for OSV API
    Removes common prefixes like 'v', '=', etc.
    """
    if not version:
        return ''
    version = version.strip()
    # Remove 'v' prefix if present
    if version.startswith('v'):
        version = version[1:]
    # Remove '=' prefix if present
    if version.startswith('='):
        version = version[1:]
    # Remove leading/trailing whitespace
    version = version.strip()
    return version


def query_batch(packages: List[Dict[str, str]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Query OSV.dev API for vulnerabilities in batch
    
    Args:
        packages: List of dicts with keys: 'name', 'version', 'manager'
    
    Returns:
        Dict mapping package identifier (manager:name:version) to list of vulnerabilities
    """
    if not packages:
        return {}
    
    # Group packages by manager for better organization
    # Create queries for OSV API
    queries = []
    package_map = {}  # Map query index to package identifier
    
    for idx, pkg in enumerate(packages):
        manager = pkg.get('manager', '')
        name = pkg.get('name', '')
        version = pkg.get('version', '')
        
        if not name or not manager:
            continue
        
        ecosystem = get_ecosystem(manager)
        if not ecosystem:
            continue
        
        normalized_version = normalize_version(version)
        if not normalized_version:
            continue
        
        # Create query for OSV API
        query = {
            'package': {
                'name': name,
                'ecosystem': ecosystem
            },
            'version': normalized_version
        }
        
        queries.append(query)
        # Create unique identifier for this package
        pkg_id = f"{manager}:{name}:{version}"
        package_map[len(queries) - 1] = pkg_id
    
    if not queries:
        return {}
    
    # Process in batches of BATCH_SIZE
    results = {}
    
    for batch_start in range(0, len(queries), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(queries))
        batch_queries = queries[batch_start:batch_end]
        
        # Create batch request
        request_data = {
            'queries': batch_queries
        }
        
        # Check cache first
        cache_key = f"osv_batch_{hash(json.dumps(request_data, sort_keys=True))}"
        cached_result = cache.get(cache_key)
        if cached_result:
            # Merge cached results
            for pkg_id, vulns in cached_result.items():
                results[pkg_id] = vulns
            continue
        
        # Make API request
        try:
            req = urllib.request.Request(
                OSV_BATCH_ENDPOINT,
                data=json.dumps(request_data).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                
                # Process results
                batch_results = response_data.get('results', [])
                for idx, result in enumerate(batch_results):
                    query_idx = batch_start + idx
                    if query_idx in package_map:
                        pkg_id = package_map[query_idx]
                        vulns = result.get('vulns', [])
                        
                        # Format vulnerabilities
                        formatted_vulns = []
                        for vuln in vulns:
                            severity_info = _extract_severity(vuln)
                            # Handle None values properly
                            summary = vuln.get('summary') or ''
                            details = vuln.get('details') or ''
                            formatted_vuln = {
                                'id': vuln.get('id', ''),
                                'summary': summary,
                                'details': details,
                                'aliases': vuln.get('aliases', []),
                                'severity': severity_info.get('severity', 'UNKNOWN'),
                                'cvss_score': severity_info.get('cvss_score'),
                                'cvss_vector': severity_info.get('cvss_vector'),
                                'modified': vuln.get('modified', ''),
                                'published': vuln.get('published', ''),
                                'references': vuln.get('references', []),
                            }
                            formatted_vulns.append(formatted_vuln)
                        
                        results[pkg_id] = formatted_vulns
                
                # Cache the batch result
                batch_cache_key = f"osv_batch_{hash(json.dumps(request_data, sort_keys=True))}"
                batch_results_dict = {}
                for idx, result in enumerate(batch_results):
                    query_idx = batch_start + idx
                    if query_idx in package_map:
                        pkg_id = package_map[query_idx]
                        vulns = result.get('vulns', [])
                        formatted_vulns = []
                        for vuln in vulns:
                            severity_info = _extract_severity(vuln)
                            # Handle None values properly
                            summary = vuln.get('summary') or ''
                            details = vuln.get('details') or ''
                            formatted_vuln = {
                                'id': vuln.get('id', ''),
                                'summary': summary,
                                'details': details,
                                'aliases': vuln.get('aliases', []),
                                'severity': severity_info.get('severity', 'UNKNOWN'),
                                'cvss_score': severity_info.get('cvss_score'),
                                'cvss_vector': severity_info.get('cvss_vector'),
                                'modified': vuln.get('modified', ''),
                                'published': vuln.get('published', ''),
                                'references': vuln.get('references', []),
                            }
                            formatted_vulns.append(formatted_vuln)
                        batch_results_dict[pkg_id] = formatted_vulns
                
                cache.set(batch_cache_key, batch_results_dict, timeout=CACHE_TIMEOUT)
        
        except urllib.error.HTTPError as e:
            # Log error but continue with other batches
            print(f"OSV API HTTP error: {e.code} - {e.reason}")
            continue
        except urllib.error.URLError as e:
            print(f"OSV API URL error: {e.reason}")
            continue
        except Exception as e:
            print(f"OSV API error: {str(e)}")
            continue
        
        # Small delay between batches to be respectful
        if batch_end < len(queries):
            time.sleep(0.5)
    
    return results


def _calculate_cvss_base_score(vector: str) -> float:
    """
    Calculate CVSS 3.x base score from vector string
    This is a simplified calculation - full CVSS calculation is complex
    Returns approximate base score
    """
    if not vector or 'CVSS' not in vector:
        return 0.0
    
    try:
        # Extract key metrics from vector
        # AV: Attack Vector (N=Network, A=Adjacent, L=Local, P=Physical)
        # AC: Attack Complexity (L=Low, H=High)
        # PR: Privileges Required (N=None, L=Low, H=High)
        # UI: User Interaction (N=None, R=Required)
        # S: Scope (U=Unchanged, C=Changed)
        # C: Confidentiality (H=High, L=Low, N=None)
        # I: Integrity (H=High, L=Low, N=None)
        # A: Availability (H=High, L=Low, N=None)
        
        av_match = re.search(r'/AV:([NALP])', vector)
        ac_match = re.search(r'/AC:([LH])', vector)
        pr_match = re.search(r'/PR:([NLH])', vector)
        ui_match = re.search(r'/UI:([NR])', vector)
        s_match = re.search(r'/S:([UC])', vector)
        c_match = re.search(r'/C:([LHN])', vector)
        i_match = re.search(r'/I:([LHN])', vector)
        a_match = re.search(r'/A:([LHN])', vector)
        
        # Simplified scoring (approximate)
        # This is not a full CVSS calculation but gives a reasonable estimate
        impact_score = 0.0
        c_val = c_match.group(1) if c_match else 'N'
        i_val = i_match.group(1) if i_match else 'N'
        a_val = a_match.group(1) if a_match else 'N'
        
        # Impact calculation (simplified)
        if c_val == 'H' or i_val == 'H' or a_val == 'H':
            if c_val == 'H' and i_val == 'H' and a_val == 'H':
                impact_score = 6.0  # High impact
            elif (c_val == 'H' and i_val == 'H') or (c_val == 'H' and a_val == 'H') or (i_val == 'H' and a_val == 'H'):
                impact_score = 5.5  # Medium-High impact
            else:
                impact_score = 4.0  # Medium impact
        elif c_val == 'L' or i_val == 'L' or a_val == 'L':
            impact_score = 2.0  # Low impact
        else:
            impact_score = 0.0  # None
        
        # Adjust for scope
        s_val = s_match.group(1) if s_match else 'U'
        if s_val == 'C':  # Changed scope increases impact
            impact_score *= 1.08
        
        # Adjust for attack vector and complexity (simplified)
        av_val = av_match.group(1) if av_match else 'N'
        ac_val = ac_match.group(1) if ac_match else 'H'
        pr_val = pr_match.group(1) if pr_match else 'N'
        ui_val = ui_match.group(1) if ui_match else 'N'
        
        # Exploitability multiplier (simplified)
        exploit_mult = 1.0
        if av_val == 'N':  # Network
            exploit_mult = 0.85
        elif av_val == 'A':  # Adjacent
            exploit_mult = 0.62
        elif av_val == 'L':  # Local
            exploit_mult = 0.55
        
        if ac_val == 'H':  # High complexity
            exploit_mult *= 0.44
        
        if pr_val == 'H':  # High privileges
            exploit_mult *= 0.27
        elif pr_val == 'L':  # Low privileges
            exploit_mult *= 0.62
        
        if ui_val == 'R':  # Required
            exploit_mult *= 0.62
        
        # Base score approximation
        base_score = min(10.0, impact_score * exploit_mult)
        
        return round(base_score, 1)
    except Exception:
        return 0.0


def _extract_severity(vuln: Dict[str, Any]) -> Dict[str, Any]:
    """Extract severity information from vulnerability data"""
    result = {
        'severity': 'UNKNOWN',
        'cvss_score': None,
        'cvss_vector': None,
    }
    
    # Check database_specific first
    db_specific = vuln.get('database_specific', {})
    if isinstance(db_specific, dict):
        severity = db_specific.get('severity', '')
        if severity:
            result['severity'] = severity.upper()
            return result
    
    # Check severity array
    severity_array = vuln.get('severity', [])
    if isinstance(severity_array, list) and severity_array:
        # Get the first severity entry (usually CVSS_V3)
        for severity_entry in severity_array:
            if isinstance(severity_entry, dict):
                score_type = severity_entry.get('type', '')
                score = severity_entry.get('score', '')
                
                if score:
                    result['cvss_vector'] = score
                    
                    # Parse CVSS vector to extract base score
                    # Format: CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N
                    if 'CVSS' in score:
                        # Calculate base score
                        base_score = _calculate_cvss_base_score(score)
                        result['cvss_score'] = base_score
                        
                        # Extract C (Confidentiality), I (Integrity), A (Availability) values
                        c_match = re.search(r'/C:([LHN])', score)
                        i_match = re.search(r'/I:([LHN])', score)
                        a_match = re.search(r'/A:([LHN])', score)
                        
                        c_val = c_match.group(1) if c_match else 'N'
                        i_val = i_match.group(1) if i_match else 'N'
                        a_val = a_match.group(1) if a_match else 'N'
                        
                        # Determine severity based on impact values (more reliable than simplified base score)
                        # C:H + I:H = High impact, even with A:N
                        high_count = sum(1 for v in [c_val, i_val, a_val] if v == 'H')
                        
                        if high_count >= 2:
                            # 2 or more High impacts = HIGH severity
                            result['severity'] = 'HIGH'
                        elif high_count == 1:
                            # 1 High impact = MEDIUM severity
                            result['severity'] = 'MEDIUM'
                        elif c_val == 'L' or i_val == 'L' or a_val == 'L':
                            # At least one Low impact = MEDIUM severity
                            result['severity'] = 'MEDIUM'
                        else:
                            # All None = LOW severity
                            result['severity'] = 'LOW'
                        
                        # If base score was calculated and is very high, upgrade to CRITICAL
                        if base_score >= 9.0:
                            result['severity'] = 'CRITICAL'
                        elif base_score >= 7.0 and result['severity'] != 'CRITICAL':
                            # If base score suggests HIGH, ensure it's at least HIGH
                            if result['severity'] == 'LOW' or result['severity'] == 'MEDIUM':
                                result['severity'] = 'HIGH'
                        
                        break
    
    return result


def scan_packages(packages_by_manager: Dict[str, List[Dict[str, str]]]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """
    Scan packages from multiple managers for CVEs
    Each manager's packages are queried in separate batches
    
    Args:
        packages_by_manager: Dict mapping manager name to list of packages
                            Each package dict should have 'name' and 'version'
    
    Returns:
        Dict mapping manager name to dict of package vulnerabilities
        Format: {manager: {package_name: [vulns]}}
    """
    results_by_manager = {}
    
    # Process each manager separately
    for manager, packages in packages_by_manager.items():
        if not packages:
            results_by_manager[manager] = {}
            continue
        
        # Prepare packages for this manager
        manager_packages = []
        for pkg in packages:
            manager_packages.append({
                'name': pkg.get('name', ''),
                'version': pkg.get('version', ''),
                'manager': manager
            })
        
        # Query OSV API for this manager's packages
        try:
            vulnerability_results = query_batch(manager_packages)
            
            # Organize results for this manager
            manager_results = {}
            for pkg_id, vulns in vulnerability_results.items():
                # Parse package identifier: manager:name:version
                parts = pkg_id.split(':', 2)
                if len(parts) >= 2:
                    name = parts[1]
                    manager_results[name] = vulns
            
            results_by_manager[manager] = manager_results
        except Exception as e:
            # If one manager fails, continue with others
            print(f"Error scanning packages for {manager}: {str(e)}")
            results_by_manager[manager] = {}
    
    return results_by_manager


def get_package_cves(manager: str, name: str, version: str) -> List[Dict[str, Any]]:
    """
    Get CVEs for a single package
    
    Args:
        manager: Package manager name
        name: Package name
        version: Package version
    
    Returns:
        List of vulnerability dicts
    """
    packages = [{'name': name, 'version': version, 'manager': manager}]
    results = query_batch(packages)
    
    pkg_id = f"{manager}:{name}:{version}"
    return results.get(pkg_id, [])

