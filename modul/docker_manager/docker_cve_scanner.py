import logging
import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple

import docker
import requests
from django.utils.translation import gettext_lazy as _

# Import main CVE scanner modules
from modul.cve_scanner.os import arch as arch_os
from modul.cve_scanner.os import debian as debian_os
from modul.cve_scanner.os import ubuntu as ubuntu_os
from modul.cve_scanner.os import fedora as fedora_os
from modul.cve_scanner.os import suse as suse_os


logger = logging.getLogger(__name__)


def _get_docker_client() -> Optional[docker.DockerClient]:
    """Docker client helper (simple version compatible with Docker Manager)."""
    try:
        return docker.from_env()
    except Exception as exc:  # pragma: no cover - only for runtime environment
        logger.error("Failed to create Docker client: %s", exc, exc_info=True)
        return None


def detect_container_os(container) -> Optional[str]:
    """
    Detect OS by reading /etc/os-release file inside container.

    Returns arch / fedora / ubuntu / debian or None.
    """
    try:
        exec_result = container.exec_run(
            "cat /etc/os-release",
            stdout=True,
            stderr=True,
        )
        content = (exec_result.output or b"").decode("utf-8", errors="ignore").lower()
    except Exception as exc:
        logger.error("Error during container OS detection: %s", exc, exc_info=True)
        return None

    if "id=arch" in content or "arch linux" in content:
        return "arch"
    if "id=fedora" in content or "fedora" in content:
        return "fedora"
    if "id=ubuntu" in content or "ubuntu" in content:
        return "ubuntu"
    if "id=debian" in content or "debian" in content:
        return "debian"
    if "id=opensuse" in content or "opensuse" in content or "suse" in content:
        return "suse"

    return None


def _get_packages_arch(container) -> List[Dict[str, str]]:
    """Get packages from container using pacman -Q."""
    try:
        exec_result = container.exec_run(
            "pacman -Q",
            stdout=True,
            stderr=True,
        )
        output = (exec_result.output or b"").decode("utf-8", errors="ignore")
        # Reuse existing Arch parser
        return arch_os._parse_pacman_q_output(output)  # type: ignore[attr-defined]
    except Exception as exc:
        logger.error("Error getting Arch container packages: %s", exc, exc_info=True)
        return []


def _get_packages_debian_like(container) -> List[Dict[str, str]]:
    """Get packages from container using dpkg -l (Debian / Ubuntu)."""
    try:
        exec_result = container.exec_run(
            "dpkg -l",
            stdout=True,
            stderr=True,
        )
        output = (exec_result.output or b"").decode("utf-8", errors="ignore")
        # Both Debian and Ubuntu use the same dpkg parser
        return debian_os._parse_dpkg_output(output)  # type: ignore[attr-defined]
    except Exception as exc:
        logger.error("Error getting Debian/Ubuntu container packages: %s", exc, exc_info=True)
        return []


def _get_packages_fedora_like(container) -> List[Dict[str, str]]:
    """Get packages from container using rpm -qa (Fedora / RHEL family)."""
    try:
        exec_result = container.exec_run(
            'rpm -qa --queryformat "%{NAME}\\t%{VERSION}-%{RELEASE}\\n"',
            stdout=True,
            stderr=True,
        )
        output = (exec_result.output or b"").decode("utf-8", errors="ignore")
        return fedora_os._parse_rpm_output(output)  # type: ignore[attr-defined]
    except Exception as exc:
        logger.error("Error getting Fedora container packages: %s", exc, exc_info=True)
        return []


def _get_packages_suse_like(container) -> List[Dict[str, str]]:
    """Get packages from container using rpm -qa (SUSE / openSUSE)."""
    # Try command first (if shell is available)
    try:
        exec_result = _exec_in_container(container, 'rpm -qa --queryformat "%{NAME}\\t%{VERSION}-%{RELEASE}\\n"')
        if exec_result and exec_result.exit_code == 0:
            output = (exec_result.output or b"").decode("utf-8", errors="ignore")
            packages = suse_os._parse_rpm_output(output)  # type: ignore[attr-defined]
            if packages:
                logger.info("Got %d packages from rpm command", len(packages))
                return packages
    except Exception as exc:
        logger.debug("rpm command failed: %s", exc)
    
    # If no shell, read from RPM database
    logger.info("Shell not available, trying to read from RPM database")
    try:
        packages = _get_packages_from_rpmdb(container)
        if packages:
            logger.info("Got %d packages from RPM database", len(packages))
            return packages
    except Exception as exc:
        logger.warning("RPM database read failed: %s", exc)
    
    logger.error("Could not get packages from SUSE container")
    return []


def _read_file_from_container(container, file_path: str) -> Optional[bytes]:
    """
    Try to read file from container (does not require shell).
    Use get_archive first, if it fails try cat command.
    Returns bytes (binary data) for binary files like SQLite databases.
    """
    # Method 1: Use Docker get_archive API (does not require shell)
    try:
        bits, stat = container.get_archive(file_path)
        # bits is a generator, read the content
        content = b''
        for chunk in bits:
            content += chunk
        
        # Comes in tar file format, extract it
        import tarfile
        import io
        tar_stream = io.BytesIO(content)
        with tarfile.open(fileobj=tar_stream, mode='r|*') as tar:
            for member in tar:
                if member.isfile():
                    file_obj = tar.extractfile(member)
                    if file_obj:
                        return file_obj.read()
    except Exception as exc:
        logger.debug("get_archive failed for %s: %s", file_path, exc)
    
    # Method 2: Try with cat command (requires shell but simpler)
    try:
        exec_result = _exec_in_container(container, f'cat {file_path}')
        if exec_result and exec_result.exit_code == 0:
            return exec_result.output if isinstance(exec_result.output, bytes) else exec_result.output.encode('utf-8')
    except Exception as exc:
        logger.debug("cat command failed for %s: %s", file_path, exc)
    
    return None


def _get_packages_from_rpmdb(container) -> List[Dict[str, str]]:
    """
    Read package list from RPM database in containers without shell.
    Reads /var/lib/rpm/rpmdb.sqlite file.
    """
    packages = []
    
    # SQLite RPM database (/var/lib/rpm/rpmdb.sqlite)
    try:
        import sqlite3
        import tempfile
        import os
        
        # Read file from container (binary)
        content = _read_file_from_container(container, '/var/lib/rpm/rpmdb.sqlite')
        if content:
            # Write to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite') as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            try:
                # Read SQLite database
                conn = sqlite3.connect(tmp_path)
                cursor = conn.cursor()
                # Check RPM SQLite database structure
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Find package table (usually 'Packages' or 'packages')
                table_name = None
                for table in ['Packages', 'packages', 'rpmdb']:
                    if table in tables:
                        table_name = table
                        break
                
                if table_name:
                    # Check table structure
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    # Find name, version, release columns
                    name_col = 'name' if 'name' in columns else (columns[0] if columns else None)
                    version_col = 'version' if 'version' in columns else (columns[1] if len(columns) > 1 else None)
                    release_col = 'release' if 'release' in columns else (columns[2] if len(columns) > 2 else None)
                    
                    if name_col and version_col:
                        query = f"SELECT {name_col}, {version_col}"
                        if release_col:
                            query += f", {release_col}"
                        query += f" FROM {table_name}"
                        
                        cursor.execute(query)
                        for row in cursor.fetchall():
                            name = row[0]
                            version = row[1] if len(row) > 1 else ''
                            release = row[2] if len(row) > 2 else ''
                            packages.append({
                                'name': name,
                                'version': f"{version}-{release}" if release else version
                            })
                
                conn.close()
                logger.info("Read %d packages from SQLite RPM database", len(packages))
            except Exception as exc:
                logger.warning("SQLite RPM database parse failed: %s", exc)
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
        else:
            logger.debug("Could not read /var/lib/rpm/rpmdb.sqlite from container")
    except Exception as exc:
        logger.debug("SQLite RPM database read failed: %s", exc)
    
    return packages


def _exec_in_container(container, command: str) -> Optional[Any]:
    """
    Execute command in container with shell.
    Finds and uses shell to work in containers without shell as well.
    """
    # Try direct command first (may be in PATH or work if shell exists)
    try:
        exec_result = container.exec_run(
            command,
            stdout=True,
            stderr=True,
        )
        # Exit code 0 olmasa bile sonucu dön (hata mesajı için)
        return exec_result
    except Exception as exc:
        logger.debug("Direct command execution failed: %s", exc)
    
    # Try shells in order
    shells = ['/bin/sh', '/bin/bash', '/usr/bin/sh', '/usr/bin/bash']
    for shell in shells:
        try:
            # Try to execute command with shell
            exec_result = container.exec_run(
                [shell, '-c', command],
                stdout=True,
                stderr=True,
            )
            # Exit code 0 olmasa bile sonucu dön (hata mesajı için)
            return exec_result
        except Exception as exc:
            logger.debug("Shell %s execution failed: %s", shell, exc)
            continue
    
    # If none worked, return None
    logger.warning("Could not execute command '%s' in container (no shell available)", command)
    return None


def _get_patches_from_filesystem(container) -> List[Dict[str, Any]]:
    """
    Read patch metadata files from filesystem in containers without shell.
    In SUSE/openSUSE, patch information is usually stored under /var/cache/zypp/ or /var/lib/zypp/.
    Simulates output produced by zypper commands when shell is available.
    """
    patches = []
    
    # Method 1: Read patch XML files from container filesystem
    # In SUSE/openSUSE, patch information is stored in repository metadata
    repo_dirs = [
        '/var/cache/zypp/raw',
        '/var/lib/zypp/repos.d',
    ]
    
    for repo_dir in repo_dirs:
        try:
            # Get directory contents (with ls command - requires shell but simpler)
            exec_result = _exec_in_container(container, f'ls -1 {repo_dir} 2>/dev/null || true')
            if exec_result and exec_result.exit_code == 0:
                output = (exec_result.output or b"").decode("utf-8", errors="ignore")
                for line in output.splitlines():
                    repo_name = line.strip()
                    if repo_name and not repo_name.startswith('.'):
                        # Check patches.xml file for each repo
                        patches_xml_path = f"{repo_dir}/{repo_name}/patches.xml"
                        content = _read_file_from_container(container, patches_xml_path)
                        if content:
                            try:
                                # Parse XML
                                xml_content = content.decode('utf-8', errors="ignore") if isinstance(content, bytes) else content
                                root = ET.fromstring(xml_content)
                                # Parse patches
                                for patch_elem in root.findall('.//patch'):
                                    patch_name = patch_elem.get('name', '')
                                    category = patch_elem.get('category', '')
                                    severity = patch_elem.get('severity', '')
                                    
                                    # Only get security patches
                                    if category.lower() == 'security':
                                        # Find CVE information
                                        cve_id = ''
                                        description = ''
                                        for info_elem in patch_elem.findall('.//information'):
                                            desc_text = info_elem.text or ''
                                            if desc_text:
                                                description = desc_text
                                                # Extract CVE ID from description
                                                cve_match = re.search(r'CVE-\d{4}-\d{4,}', desc_text, re.IGNORECASE)
                                                if cve_match:
                                                    cve_id = cve_match.group(0)
                                        
                                        # Also get description from summary
                                        for summary_elem in patch_elem.findall('.//summary'):
                                            summary_text = summary_elem.text or ''
                                            if summary_text and not description:
                                                description = summary_text
                                                cve_match = re.search(r'CVE-\d{4}-\d{4,}', summary_text, re.IGNORECASE)
                                                if cve_match:
                                                    cve_id = cve_match.group(0)
                                        
                                        if patch_name:
                                            patches.append({
                                                'cve': cve_id,
                                                'patch': patch_name,
                                                'category': category,
                                                'severity': severity,
                                                'status': 'needed',
                                                'description': description,
                                            })
                                            logger.debug("Found patch from filesystem: %s (CVE: %s)", patch_name, cve_id)
                            except ET.ParseError as exc:
                                logger.debug("Failed to parse patches.xml from %s: %s", patches_xml_path, exc)
                            except Exception as exc:
                                logger.debug("Failed to process patches.xml from %s: %s", patches_xml_path, exc)
        except Exception as exc:
            logger.debug("Failed to read repo dir %s: %s", repo_dir, exc)
    
    # Method 2: If XML files don't exist, we could try reading zypp solv files
    # But these are binary format, difficult to parse
    
    logger.info("Found %d patches from filesystem", len(patches))
    return patches


def _get_patches_from_api(packages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Get CVE information using openSUSE Security API or NVD API.
    Note: This API provides general CVE information, needs to be matched with package versions in container.
    """
    patches = []
    
    # Method 1: Use NVD (National Vulnerability Database) API
    # This provides general CVE information, needs to be matched with package names
    try:
        # NVD API endpoint
        nvd_api_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        
        # Select important packages from installed ones (querying all packages would be too slow)
        # Only check common packages
        important_packages = [pkg['name'] for pkg in packages[:50]]  # Check first 50 packages
        
        for pkg_name in important_packages:
            try:
                # Search CVE by package name in NVD API
                # Note: NVD API doesn't search directly by package name, searches in CVE description
                # Therefore this method is not very efficient
                params = {
                    'keywordSearch': pkg_name,
                    'resultsPerPage': 20,
                }
                response = requests.get(nvd_api_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    vulnerabilities = data.get('vulnerabilities', [])
                    for vuln in vulnerabilities:
                        cve_item = vuln.get('cve', {})
                        cve_id = cve_item.get('id', '')
                        descriptions = cve_item.get('descriptions', [])
                        description = descriptions[0].get('value', '') if descriptions else ''
                        
                        # Check if package name appears in CVE description
                        if pkg_name.lower() in description.lower():
                            # Get severity information
                            metrics = cve_item.get('metrics', {})
                            severity = 'unknown'
                            if 'cvssMetricV31' in metrics:
                                severity = metrics['cvssMetricV31'][0].get('cvssData', {}).get('baseSeverity', 'unknown')
                            elif 'cvssMetricV30' in metrics:
                                severity = metrics['cvssMetricV30'][0].get('cvssData', {}).get('baseSeverity', 'unknown')
                            
                            patches.append({
                                'cve': cve_id,
                                'patch': f'SUSE-{cve_id}',
                                'category': 'security',
                                'severity': severity.lower() if severity else 'unknown',
                                'status': 'open',
                                'description': description,
                                'package_hint': pkg_name,  # Which package it was found for
                            })
            except Exception as exc:
                logger.debug("NVD API query failed for package %s: %s", pkg_name, exc)
                continue
    except Exception as exc:
        logger.debug("NVD API method failed: %s", exc)
    
    logger.info("Found %d patches from API", len(patches))
    return patches


def _get_patch_packages_container(container, patch_name: str) -> List[str]:
    """
    Find packages affected by patch in container.
    """
    packages = []
    try:
        exec_result = _exec_in_container(container, f'zypper --non-interactive info -t patch {patch_name}')
        if exec_result and exec_result.exit_code == 0:
            output = (exec_result.output or b"").decode("utf-8", errors="ignore")
            logger.debug("zypper info -t patch %s output (first 1000 chars): %s", patch_name, output[:1000])
            
            for line in output.splitlines():
                line = line.strip()
                # Extract package names from "Provides:" lines
                # Example: "Provides: glib2 = 2.78.4-150600.3.1" or "Provides: libglib-2_0-0 = 2.78.4-150600.3.1"
                if 'Provides:' in line:
                    # "Provides: glib2 = 2.78.4" -> "glib2"
                    # "Provides: libglib-2_0-0 = 2.78.4" -> "libglib-2_0-0"
                    match = re.search(r'Provides:\s*(\S+)\s*[=<>]', line, re.IGNORECASE)
                    if match:
                        pkg_name = match.group(1)
                        if pkg_name and pkg_name not in packages:
                            packages.append(pkg_name)
                            logger.debug("Found package from Provides: %s", pkg_name)
                
                # Also extract package names from "Requires:" lines
                if 'Requires:' in line:
                    match = re.search(r'Requires:\s*(\S+)\s*[=<>]', line, re.IGNORECASE)
                    if match:
                        pkg_name = match.group(1)
                        if pkg_name and pkg_name not in packages:
                            packages.append(pkg_name)
                            logger.debug("Found package from Requires: %s", pkg_name)
                
                # Also extract package name from "Information:" or "Summary:" lines
                # Example: "Information: Security update for glib2"
                if ('Information:' in line or 'Summary:' in line) and 'for ' in line.lower():
                    match = re.search(r'for\s+(\S+)', line, re.IGNORECASE)
                    if match:
                        pkg_name = match.group(1).strip()
                        # Clean punctuation marks
                        pkg_name = re.sub(r'[^\w\-]', '', pkg_name)
                        if pkg_name and pkg_name not in ['the', 'a', 'an', 'this', 'that', 'update', 'security'] and pkg_name not in packages:
                            packages.append(pkg_name)
                            logger.debug("Found package from Information/Summary: %s", pkg_name)
    except Exception as exc:
        logger.warning("Error getting patch packages for %s: %s", patch_name, exc)
    return packages


def _scan_suse_container(container, packages: List[Dict[str, str]]) -> Tuple[Dict[str, Any], int]:
    """
    Special CVE scanning for SUSE container.
    Finds CVEs by running zypper commands inside container.
    Uses parse functions from suse.py.
    Uses filesystem or API in containers without shell.
    """
    all_patches: List[Dict[str, Any]] = []
    
    # Shell check: Try to run zypper commands
    # In SUSE containers, zypper commands don't work without shell
    shell_available = False
    try:
        test_result = _exec_in_container(container, 'zypper --version')
        if test_result and test_result.exit_code == 0:
            # Check output - is it really zypper output?
            output = (test_result.output or b"").decode("utf-8", errors="ignore")
            if output and ('zypper' in output.lower() or 'suse' in output.lower() or len(output.strip()) > 10):
                shell_available = True
                logger.info("Shell available - zypper command succeeded")
            else:
                logger.warning("zypper --version returned empty or invalid output, assuming no shell")
                shell_available = False
        else:
            logger.warning("zypper --version failed with exit_code %s, assuming no shell", 
                          test_result.exit_code if test_result else 'None')
            shell_available = False
    except Exception as exc:
        logger.warning("zypper --version test failed with exception: %s, assuming no shell", exc)
        shell_available = False
    
    if not shell_available:
        logger.warning("Shell not available in SUSE container - CVE scanning may be incomplete or inaccurate")
        # Read patch metadata from filesystem in containers without shell
        patches_from_filesystem = _get_patches_from_filesystem(container)
        if patches_from_filesystem:
            logger.info("Found %d patches from filesystem", len(patches_from_filesystem))
            all_patches.extend(patches_from_filesystem)
        else:
            logger.warning("Could not read patch metadata from filesystem, falling back to API")
            # API fallback: Use openSUSE Security API
            patches_from_api = _get_patches_from_api(packages)
            if patches_from_api:
                logger.info("Found %d patches from API", len(patches_from_api))
                all_patches.extend(patches_from_api)
        
        if not all_patches:
            logger.warning("No patches found via filesystem or API")
            return {
                "total_installed": len(packages),
                "total_advisories": 0,
                "total_matched": 0,
                "matched": [],
                "shell_available": shell_available
            }, 200
        # Patches found but add warning because no shell
        # We'll add warning to results (when returning below)
    
    # Method 1: zypper list-patches --cve (with CVE IDs)
    # Shell check: If no shell, zypper commands won't work
    if shell_available:
        try:
            exec_result = _exec_in_container(container, 'zypper --non-interactive list-patches --cve')
            if exec_result:
                logger.info("zypper list-patches --cve exit_code: %s", exec_result.exit_code)
                if exec_result.exit_code == 0:
                    output = (exec_result.output or b"").decode("utf-8", errors="ignore")
                    logger.debug("zypper list-patches --cve output (first 500 chars): %s", output[:500])
                    # suse.py'deki parse fonksiyonunu kullan
                    patches = suse_os._parse_zypper_list_patches_cve(output)  # type: ignore[attr-defined]
                    logger.info("Parsed %d patches from zypper list-patches --cve", len(patches))
                    all_patches.extend(patches)
                else:
                    stderr = (exec_result.output or b"").decode("utf-8", errors="ignore")
                    logger.warning("zypper list-patches --cve failed with exit_code %s: %s", exec_result.exit_code, stderr[:200])
                    # If zypper command fails, shell may not be available
                    if exec_result.exit_code != 0:
                        logger.warning("zypper command failed, marking shell as unavailable")
                        shell_available = False
            else:
                logger.warning("zypper list-patches --cve: Could not execute command (no shell available?)")
                shell_available = False
        except Exception as exc:
            logger.error("zypper list-patches --cve exception: %s", exc, exc_info=True)
            shell_available = False
    
    # Method 2: zypper lu -t patch (security patches)
    # Only run if shell is available
    if shell_available:
        try:
            exec_result = _exec_in_container(container, 'zypper --non-interactive lu -t patch')
            if exec_result:
                logger.info("zypper lu -t patch exit_code: %s", exec_result.exit_code)
                if exec_result.exit_code == 0:
                    output = (exec_result.output or b"").decode("utf-8", errors="ignore")
                    logger.debug("zypper lu -t patch output (first 500 chars): %s", output[:500])
                    # suse.py'deki parse fonksiyonunu kullan
                    patches = suse_os._parse_zypper_lu_patch_security(output)  # type: ignore[attr-defined]
                    logger.info("Parsed %d patches from zypper lu -t patch", len(patches))
                    # Duplicate check
                    for patch in patches:
                        existing = next((p for p in all_patches if p.get('patch') == patch.get('patch')), None)
                        if not existing:
                            all_patches.append(patch)
                else:
                    stderr = (exec_result.output or b"").decode("utf-8", errors="ignore")
                    logger.warning("zypper lu -t patch failed with exit_code %s: %s", exec_result.exit_code, stderr[:200])
                    # If zypper command fails, shell may not be available
                    if exec_result.exit_code != 0:
                        logger.warning("zypper command failed, marking shell as unavailable")
                        shell_available = False
            else:
                logger.warning("zypper lu -t patch: Could not execute command (no shell available?)")
                shell_available = False
        except Exception as exc:
            logger.error("zypper lu -t patch exception: %s", exc, exc_info=True)
            shell_available = False
    
    logger.info("Total patches found: %d", len(all_patches))
    
        # Find and match affected packages for each patch
    matched: List[Dict[str, Any]] = []
    
    logger.info("Processing %d patches against %d installed packages", len(all_patches), len(packages))
    
    for patch in all_patches:
        patch_name = patch.get('patch', '')
        cve_id = patch.get('cve', '').strip()
        severity = patch.get('severity', '')
        description = patch.get('description', '')
        
        logger.debug("Processing patch: %s, CVE: %s, Description: %s", patch_name, cve_id, description)
        
        # Find packages affected by patch in container
        # Use zypper info if shell is available, otherwise extract only from description
        # Note: shell_available variable was already determined at function start
        affected_packages = []
        
        if shell_available:
            affected_packages = _get_patch_packages_container(container, patch_name)
            logger.debug("Patch %s affects packages (from zypper info): %s", patch_name, affected_packages)
        else:
            logger.debug("Shell not available, will extract package from description only")
        
        # If we can't find package from zypper info, extract from description
        if not affected_packages and description:
            # "Security update for glib2" -> "glib2"
            # "Recommended update for gpgme" -> "gpgme"
            desc_lower = description.lower()
            if 'for ' in desc_lower:
                # Like "for glib2" or "for gpgme"
                match = re.search(r'for\s+(\S+)', description, re.IGNORECASE)
                if match:
                    pkg_name = match.group(1).strip()
                    # Clean package name (remove punctuation marks)
                    pkg_name = re.sub(r'[^\w\-]', '', pkg_name)
                    if pkg_name and pkg_name not in ['the', 'a', 'an', 'this', 'that', 'update', 'security']:
                        affected_packages.append(pkg_name)
                        logger.debug("Extracted package from description: %s", pkg_name)
        
        # If we still can't find package, skip patch
        if not affected_packages:
            logger.warning("No packages found for patch %s (description: %s), skipping", patch_name, description)
            continue
        
        # Format CVE ID
        if not cve_id or not cve_id.startswith('CVE-'):
            cve_match = re.search(r'CVE-\d{4}-\d{4,}', description, re.IGNORECASE)
            if cve_match:
                cve_id = cve_match.group(0)
            else:
                cve_id = f'SUSE-{patch_name}'
        
        logger.debug("Final CVE ID: %s, Affected packages: %s", cve_id, affected_packages)
        
        # Match with installed packages
        for package in packages:
            package_name = package['name']
            package_version = package['version']
            
            # Package name matching (case-insensitive)
            # Try exact match first, then partial match (glib2 -> glib2-32bit, glib2-devel, etc.)
            for affected_pkg in affected_packages:
                pkg_name_lower = package_name.lower()
                affected_pkg_lower = affected_pkg.lower()
                
                # Exact match
                if pkg_name_lower == affected_pkg_lower:
                    logger.info("MATCH FOUND (exact): Package %s (version %s) matches patch %s (CVE: %s)", 
                              package_name, package_version, patch_name, cve_id)
                    matched.append({
                        'advisory': cve_id,
                        'package': package_name,
                        'installed_version': package_version,
                        'affected': package_version,
                        'fixed': '',
                        'issues': [cve_id] if cve_id.startswith('CVE-') else [],
                        'severity': severity,
                        'status': 'open',
                        'description': description if description else f'SUSE Security Advisory: {patch_name}',
                        'patch': patch_name,
                        'source': 'SUSE Security Advisory'
                    })
                    break
                # Partial match (glib2 -> glib2-32bit, glib2-devel, libglib-2_0-0, etc.)
                elif (pkg_name_lower.startswith(affected_pkg_lower + '-') or 
                      pkg_name_lower.startswith(affected_pkg_lower + '_') or
                      pkg_name_lower.startswith('lib' + affected_pkg_lower) or
                      pkg_name_lower.startswith(affected_pkg_lower.replace('2', '2_0-0'))):
                    logger.info("MATCH FOUND (partial): Package %s (version %s) matches patch %s (CVE: %s)", 
                              package_name, package_version, patch_name, cve_id)
                    matched.append({
                        'advisory': cve_id,
                        'package': package_name,
                        'installed_version': package_version,
                        'affected': package_version,
                        'fixed': '',
                        'issues': [cve_id] if cve_id.startswith('CVE-') else [],
                        'severity': severity,
                        'status': 'open',
                        'description': description if description else f'SUSE Security Advisory: {patch_name}',
                        'patch': patch_name,
                        'source': 'SUSE Security Advisory'
                    })
                    break
                # Special SUSE package name matching
                # glib2 -> libglib-2_0-0, libglib-2_0-0-32bit, etc.
                # Basic logic: If base part of package name extracted from description appears in installed package name, match
                # Example: "glib2" -> base part "glib", "libglib-2_0-0" contains "glib"
                
                # Extract base part from package name (remove lib prefix, version numbers, special characters)
                pkg_base = pkg_name_lower
                if pkg_base.startswith('lib'):
                    pkg_base = pkg_base[3:]  # Remove lib prefix
                
                # Only take letters (glib2 -> glib, libglib-2_0-0 -> glib)
                pkg_base_clean = re.sub(r'[^a-z]', '', pkg_base)
                affected_base_clean = re.sub(r'[^a-z]', '', affected_pkg_lower)
                
                # If base names match (glib2 -> glib, libglib-2_0-0 -> glib)
                if pkg_base_clean == affected_base_clean and len(pkg_base_clean) >= 3:
                    logger.info("MATCH FOUND (SUSE naming): Package %s (version %s) matches patch %s (CVE: %s) for %s", 
                              package_name, package_version, patch_name, cve_id, affected_pkg)
                    matched.append({
                        'advisory': cve_id,
                        'package': package_name,
                        'installed_version': package_version,
                        'affected': package_version,
                        'fixed': '',
                        'issues': [cve_id] if cve_id.startswith('CVE-') else [],
                        'severity': severity,
                        'status': 'open',
                        'description': description if description else f'SUSE Security Advisory: {patch_name}',
                        'patch': patch_name,
                        'source': 'SUSE Security Advisory'
                    })
                    break
                
                # Alternative: If package name extracted from description appears in installed package name
                # Example: "glib2" -> "libglib-2_0-0" contains "glib"
                if affected_base_clean in pkg_base_clean and len(affected_base_clean) >= 3:
                    logger.info("MATCH FOUND (SUSE naming substring): Package %s (version %s) matches patch %s (CVE: %s) for %s", 
                              package_name, package_version, patch_name, cve_id, affected_pkg)
                    matched.append({
                        'advisory': cve_id,
                        'package': package_name,
                        'installed_version': package_version,
                        'affected': package_version,
                        'fixed': '',
                        'issues': [cve_id] if cve_id.startswith('CVE-') else [],
                        'severity': severity,
                        'status': 'open',
                        'description': description if description else f'SUSE Security Advisory: {patch_name}',
                        'patch': patch_name,
                        'source': 'SUSE Security Advisory'
                    })
                    break
    
    unique_advisories = {m.get("advisory", "") for m in matched if m.get("advisory")}
    
    logger.info("SUSE CVE scan complete: %d patches, %d matches, %d unique advisories", 
                len(all_patches), len(matched), len(unique_advisories))
    
    result = {
        "total_installed": len(packages),
        "total_advisories": len(unique_advisories),
        "total_matched": len(matched),
        "matched": matched,
        "shell_available": shell_available  # For showing i18n-compatible message in frontend
    }
    
    return result, 200


def _scan_with_handler(
    os_type: str, packages: List[Dict[str, str]], container=None
) -> Tuple[Dict[str, Any], int]:
    """
    Perform CVE scan on package list using relevant OS handler.

    Returned dictionary structure is similar to run_scan in main CVE scanner:
    {
        "total_installed": int,
        "total_advisories": int,
        "total_matched": int,
        "matched": List[Dict[str, Any]],
    }
    and HTTP status code (200 / 400 / 500).
    """
    if not packages:
        return {
            "total_installed": 0,
            "total_advisories": 0,
            "total_matched": 0,
            "matched": [],
        }, 200

    try:
        if os_type == "arch":
            batch_results = arch_os.scan_cves(packages)
            matched, total = arch_os.match_advisories(packages, batch_results)
            # In Arch, advisory names come from match
            unique_advisories = {m.get("advisory", "") for m in matched if m.get("advisory")}

        elif os_type == "debian":
            batch_results = debian_os.scan_cves(packages)
            matched, total = debian_os.match_advisories(packages, batch_results)
            unique_advisories = {m.get("advisory", "") for m in matched if m.get("advisory")}

        elif os_type == "ubuntu":
            batch_results = ubuntu_os.scan_cves(packages)
            matched, total = ubuntu_os.match_advisories(packages, batch_results)
            unique_advisories = {m.get("advisory", "") for m in matched if m.get("advisory")}

        elif os_type == "fedora":
            batch_results = fedora_os.scan_cves(packages)
            matched, total = fedora_os.match_advisories(packages, batch_results)
            unique_advisories = {m.get("advisory", "") for m in matched if m.get("advisory")}

        elif os_type == "suse":
            # For SUSE, run zypper commands inside container
            if container:
                return _scan_suse_container(container, packages)
            else:
                # Fallback to system scan if no container provided
                batch_results = suse_os.scan_cves(packages)
                matched, total = suse_os.match_advisories(packages, batch_results)
                unique_advisories = {m.get("advisory", "") for m in matched if m.get("advisory")}

        else:
            return {
                "error": str(_("Unsupported OS type for container CVE scan: %(os_type)s")) % {"os_type": os_type}
            }, 400

        return {
            "total_installed": len(packages),
            "total_advisories": len(unique_advisories),
            "total_matched": total,
            "matched": list(matched),
        }, 200

    except Exception as exc:
        logger.error("Error during container CVE scan: %s", exc, exc_info=True)
        return {
            "error": str(exc),
            "total_installed": len(packages),
            "total_advisories": 0,
            "total_matched": 0,
            "matched": [],
        }, 500


def scan_container_cves(container_id: str) -> Dict[str, Any]:
    """
    For given container_id:
      1) OS detection
      2) Get package list
      3) CVE scan with relevant OS handler
    """
    client = _get_docker_client()
    if not client:
        return {
            "success": False,
            "error": str(_("Docker is not available on this host")),
        }

    try:
        container = client.containers.get(container_id)
    except Exception as exc:
        logger.error("Container not found: %s", exc, exc_info=True)
        return {
            "success": False,
            "error": str(_("Container not found: %(container_id)s")) % {"container_id": container_id},
        }

    if container.status != "running":
        return {
            "success": False,
            "error": str(_("Container is not running")),
        }

    os_type = detect_container_os(container)
    if not os_type:
        return {
            "success": False,
            "error": str(_("Could not detect OS type in container")),
        }

    # Get package list according to OS type
    if os_type == "arch":
        packages = _get_packages_arch(container)
    elif os_type in ("debian", "ubuntu"):
        packages = _get_packages_debian_like(container)
    elif os_type == "fedora":
        packages = _get_packages_fedora_like(container)
    elif os_type == "suse":
        packages = _get_packages_suse_like(container)
    else:
        return {
            "success": False,
            "error": str(_("Unsupported OS type for container CVE scan: %(os_type)s")) % {"os_type": os_type},
        }

    result, status_code = _scan_with_handler(os_type, packages, container=container)

    # Return a richer response for frontend
    response: Dict[str, Any] = {
        "success": status_code == 200,
        "os_type": os_type,
        "total_installed": result.get("total_installed", 0),
        "total_advisories": result.get("total_advisories", 0),
        "total_matched": result.get("total_matched", 0),
        "matched": result.get("matched", []),
    }

    if "error" in result:
        response["error"] = result["error"]
    
    # Also add warning message (for containers without shell) - backward compatibility
    if "warning" in result:
        response["warning"] = result["warning"]
    
    # Add shell status (for showing i18n-compatible message in frontend)
    if "shell_available" in result:
        response["shell_available"] = result["shell_available"]

    return response


