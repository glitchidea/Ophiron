import logging
from typing import Dict, Any, List, Optional, Tuple

import docker

# Ana CVE tarayıcı modüllerini import ediyoruz
from modul.cve_scanner.os import arch as arch_os
from modul.cve_scanner.os import debian as debian_os
from modul.cve_scanner.os import ubuntu as ubuntu_os
from modul.cve_scanner.os import fedora as fedora_os


logger = logging.getLogger(__name__)


def _get_docker_client() -> Optional[docker.DockerClient]:
    """Docker client helper (Docker Manager ile uyumlu basit versiyon)."""
    try:
        return docker.from_env()
    except Exception as exc:  # pragma: no cover - sadece runtime ortamı için
        logger.error("Docker client oluşturulamadı: %s", exc, exc_info=True)
        return None


def detect_container_os(container) -> Optional[str]:
    """
    Container içindeki /etc/os-release dosyasını okuyarak OS tespiti yap.

    arch / fedora / ubuntu / debian döner veya None.
    """
    try:
        exec_result = container.exec_run(
            "cat /etc/os-release",
            stdout=True,
            stderr=True,
        )
        content = (exec_result.output or b"").decode("utf-8", errors="ignore").lower()
    except Exception as exc:
        logger.error("Container OS tespiti sırasında hata: %s", exc, exc_info=True)
        return None

    if "id=arch" in content or "arch linux" in content:
        return "arch"
    if "id=fedora" in content or "fedora" in content:
        return "fedora"
    if "id=ubuntu" in content or "ubuntu" in content:
        return "ubuntu"
    if "id=debian" in content or "debian" in content:
        return "debian"

    return None


def _get_packages_arch(container) -> List[Dict[str, str]]:
    """Container içinde pacman -Q ile paketleri al."""
    try:
        exec_result = container.exec_run(
            "pacman -Q",
            stdout=True,
            stderr=True,
        )
        output = (exec_result.output or b"").decode("utf-8", errors="ignore")
        # Mevcut Arch parser'ını tekrar kullanıyoruz
        return arch_os._parse_pacman_q_output(output)  # type: ignore[attr-defined]
    except Exception as exc:
        logger.error("Arch container paketleri alınırken hata: %s", exc, exc_info=True)
        return []


def _get_packages_debian_like(container) -> List[Dict[str, str]]:
    """Container içinde dpkg -l ile paketleri al (Debian / Ubuntu)."""
    try:
        exec_result = container.exec_run(
            "dpkg -l",
            stdout=True,
            stderr=True,
        )
        output = (exec_result.output or b"").decode("utf-8", errors="ignore")
        # Hem Debian hem Ubuntu aynı dpkg parser'ını kullanıyor
        return debian_os._parse_dpkg_output(output)  # type: ignore[attr-defined]
    except Exception as exc:
        logger.error("Debian/Ubuntu container paketleri alınırken hata: %s", exc, exc_info=True)
        return []


def _get_packages_fedora_like(container) -> List[Dict[str, str]]:
    """Container içinde rpm -qa ile paketleri al (Fedora / RHEL family)."""
    try:
        exec_result = container.exec_run(
            'rpm -qa --queryformat "%{NAME}\\t%{VERSION}-%{RELEASE}\\n"',
            stdout=True,
            stderr=True,
        )
        output = (exec_result.output or b"").decode("utf-8", errors="ignore")
        return fedora_os._parse_rpm_output(output)  # type: ignore[attr-defined]
    except Exception as exc:
        logger.error("Fedora container paketleri alınırken hata: %s", exc, exc_info=True)
        return []


def _scan_with_handler(
    os_type: str, packages: List[Dict[str, str]]
) -> Tuple[Dict[str, Any], int]:
    """
    İlgili OS handler'ını kullanarak paket listesi üzerinden CVE taraması yap.

    Dönen sözlük yapısı, ana CVE tarayıcıdaki run_scan ile benzer:
    {
        "total_installed": int,
        "total_advisories": int,
        "total_matched": int,
        "matched": List[Dict[str, Any]],
    }
    ve HTTP status kodu (200 / 400 / 500).
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
            # Arch'ta advisory isimleri match içinden geliyor
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

        else:
            return {
                "error": f"Unsupported OS type for container CVE scan: {os_type}"
            }, 400

        return {
            "total_installed": len(packages),
            "total_advisories": len(unique_advisories),
            "total_matched": total,
            "matched": list(matched),
        }, 200

    except Exception as exc:
        logger.error("Container CVE taraması sırasında hata: %s", exc, exc_info=True)
        return {
            "error": str(exc),
            "total_installed": len(packages),
            "total_advisories": 0,
            "total_matched": 0,
            "matched": [],
        }, 500


def scan_container_cves(container_id: str) -> Dict[str, Any]:
    """
    Verilen container_id için:
      1) OS tespiti
      2) Paket listesini alma
      3) İlgili OS handler'ı ile CVE taraması
    """
    client = _get_docker_client()
    if not client:
        return {
            "success": False,
            "error": "Docker is not available on this host",
        }

    try:
        container = client.containers.get(container_id)
    except Exception as exc:
        logger.error("Container bulunamadı: %s", exc, exc_info=True)
        return {
            "success": False,
            "error": f"Container not found: {container_id}",
        }

    if container.status != "running":
        return {
            "success": False,
            "error": "Container is not running",
        }

    os_type = detect_container_os(container)
    if not os_type:
        return {
            "success": False,
            "error": "Could not detect OS type in container",
        }

    # OS tipine göre paket listesini al
    if os_type == "arch":
        packages = _get_packages_arch(container)
    elif os_type in ("debian", "ubuntu"):
        packages = _get_packages_debian_like(container)
    elif os_type == "fedora":
        packages = _get_packages_fedora_like(container)
    else:
        return {
            "success": False,
            "error": f"Unsupported OS type for container CVE scan: {os_type}",
        }

    result, status_code = _scan_with_handler(os_type, packages)

    # Frontend için biraz daha zengin bir cevap dönelim
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

    return response


