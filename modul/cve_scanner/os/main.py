import os
from typing import Literal, Optional


def detect_os() -> Optional[Literal["arch", "fedora", "debian", "ubuntu"]]:
    os_release = "/etc/os-release"
    try:
        if os.path.exists(os_release):
            with open(os_release, "r", encoding="utf-8") as f:
                content = f.read().lower()
                # Check for Arch Linux
                if "id=arch" in content or "arch linux" in content:
                    return "arch"
                # Check for Fedora
                if "id=fedora" in content or "fedora" in content:
                    return "fedora"
                # Check for Ubuntu (check before Debian as Ubuntu is based on Debian)
                if "id=ubuntu" in content or "ubuntu" in content:
                    return "ubuntu"
                # Check for Debian
                if "id=debian" in content or "debian" in content:
                    return "debian"
    except Exception:
        pass
    return None


def get_handler():
    from . import arch, fedora, debian, ubuntu

    current = detect_os()
    if current == "arch":
        return arch
    elif current == "fedora":
        return fedora
    elif current == "ubuntu":
        return ubuntu
    elif current == "debian":
        return debian
    return None


