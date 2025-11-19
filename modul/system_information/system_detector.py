"""
System Detector Module
Detects operating system type and distribution details
Provides platform-specific feature availability flags
"""

import platform
import os
import logging

logger = logging.getLogger(__name__)


class SystemDetector:
    """
    Detects the operating system and distribution.
    Provides flags for platform-specific features.
    """
    
    def __init__(self):
        self.system = platform.system()  # 'Windows', 'Linux', 'Darwin' (macOS)
        self.release = platform.release()
        self.version = platform.version()
        self.machine = platform.machine()
        
        self.is_windows = self.system == 'Windows'
        self.is_linux = self.system == 'Linux'
        self.is_macos = self.system == 'Darwin'
        
        # Linux distribution details
        self.linux_distro = None
        self.linux_distro_version = None
        self.linux_distro_id = None
        
        if self.is_linux:
            self._detect_linux_distro()
        
        # Feature availability flags
        self.has_pwd = self._check_pwd_available()
        self.has_win32 = self._check_win32_available()
    
    def _detect_linux_distro(self):
        """
        Detects Linux distribution using multiple methods.
        Priority: platform.freedesktop_os_release() > /etc/os-release > lsb_release
        """
        try:
            # Method 1: platform.freedesktop_os_release() (Python 3.10+)
            if hasattr(platform, 'freedesktop_os_release'):
                os_info = platform.freedesktop_os_release()
                self.linux_distro = os_info.get('NAME', 'Unknown Linux')
                self.linux_distro_version = os_info.get('VERSION', 'Unknown')
                self.linux_distro_id = os_info.get('ID', 'unknown').lower()
                logger.info(f"Detected Linux distro: {self.linux_distro} {self.linux_distro_version}")
                return
        except Exception as e:
            logger.debug(f"Could not use freedesktop_os_release: {e}")
        
        # Method 2: Read /etc/os-release directly
        try:
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    lines = f.readlines()
                    os_info = {}
                    for line in lines:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            os_info[key] = value.strip('"')
                    
                    self.linux_distro = os_info.get('NAME', 'Unknown Linux')
                    self.linux_distro_version = os_info.get('VERSION', 'Unknown')
                    self.linux_distro_id = os_info.get('ID', 'unknown').lower()
                    logger.info(f"Detected Linux distro from /etc/os-release: {self.linux_distro} {self.linux_distro_version}")
                    return
        except Exception as e:
            logger.debug(f"Could not read /etc/os-release: {e}")
        
        # Method 3: Try lsb_release command
        try:
            import subprocess
            result = subprocess.run(['lsb_release', '-a'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                output = result.stdout
                for line in output.split('\n'):
                    if 'Distributor ID:' in line:
                        self.linux_distro_id = line.split(':')[1].strip().lower()
                    elif 'Description:' in line:
                        self.linux_distro = line.split(':')[1].strip()
                    elif 'Release:' in line:
                        self.linux_distro_version = line.split(':')[1].strip()
                logger.info(f"Detected Linux distro from lsb_release: {self.linux_distro} {self.linux_distro_version}")
                return
        except Exception as e:
            logger.debug(f"Could not use lsb_release: {e}")
        
        # Fallback: Generic Linux
        self.linux_distro = 'Generic Linux'
        self.linux_distro_version = 'Unknown'
        self.linux_distro_id = 'linux'
        logger.warning("Could not detect specific Linux distribution, using generic")
    
    def _check_pwd_available(self):
        """Check if pwd module is available (Unix/Linux/macOS only)"""
        try:
            import pwd
            return True
        except ImportError:
            return False
    
    def _check_win32_available(self):
        """Check if win32 modules are available (Windows only)"""
        try:
            import win32net
            import win32netcon
            return True
        except ImportError:
            return False
    
    def get_os_display_name(self):
        """Get a user-friendly OS display name"""
        if self.is_windows:
            # Windows 10, Windows 11, etc.
            return f"Windows {self.release}"
        elif self.is_linux and self.linux_distro:
            # Ubuntu 22.04, Arch Linux, Fedora 38, etc.
            if self.linux_distro_version and self.linux_distro_version != 'Unknown':
                return f"{self.linux_distro} {self.linux_distro_version}"
            return self.linux_distro
        elif self.is_macos:
            # macOS Ventura, macOS Sonoma, etc.
            return f"macOS {self.release}"
        else:
            return f"{self.system} {self.release}"
    
    def get_distro_family(self):
        """
        Get the distribution family (useful for package management, etc.)
        Returns: 'debian', 'redhat', 'arch', 'windows', 'macos', 'unknown'
        """
        if self.is_windows:
            return 'windows'
        elif self.is_macos:
            return 'macos'
        elif self.is_linux and self.linux_distro_id:
            # Debian family
            if self.linux_distro_id in ['debian', 'ubuntu', 'mint', 'pop', 'elementary', 'zorin', 'kali']:
                return 'debian'
            # RedHat family
            elif self.linux_distro_id in ['rhel', 'centos', 'fedora', 'rocky', 'almalinux', 'oracle']:
                return 'redhat'
            # Arch family
            elif self.linux_distro_id in ['arch', 'manjaro', 'endeavouros', 'garuda']:
                return 'arch'
            # SUSE family
            elif self.linux_distro_id in ['opensuse', 'suse', 'sles']:
                return 'suse'
            else:
                return 'unknown'
        return 'unknown'
    
    def get_package_manager(self):
        """Get the likely package manager for this system"""
        family = self.get_distro_family()
        
        if family == 'debian':
            return 'apt'
        elif family == 'redhat':
            return 'dnf' if self.linux_distro_id in ['fedora'] else 'yum'
        elif family == 'arch':
            return 'pacman'
        elif family == 'suse':
            return 'zypper'
        elif family == 'windows':
            return 'winget'  # or 'chocolatey'
        elif family == 'macos':
            return 'brew'
        else:
            return 'unknown'
    
    def get_system_info(self):
        """Get all system information as a dictionary"""
        return {
            'system': self.system,
            'release': self.release,
            'version': self.version,
            'machine': self.machine,
            'is_windows': self.is_windows,
            'is_linux': self.is_linux,
            'is_macos': self.is_macos,
            'os_display_name': self.get_os_display_name(),
            'distro_family': self.get_distro_family(),
            'package_manager': self.get_package_manager(),
            'has_pwd': self.has_pwd,
            'has_win32': self.has_win32,
        }
    
    def __str__(self):
        """String representation"""
        return f"SystemDetector({self.get_os_display_name()}, Family: {self.get_distro_family()})"


# Global singleton instance
_detector_instance = None

def get_system_detector():
    """Get or create the global SystemDetector instance"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = SystemDetector()
    return _detector_instance


# Convenience functions
def is_windows():
    """Quick check if running on Windows"""
    return get_system_detector().is_windows

def is_linux():
    """Quick check if running on Linux"""
    return get_system_detector().is_linux

def is_macos():
    """Quick check if running on macOS"""
    return get_system_detector().is_macos

def has_pwd_module():
    """Quick check if pwd module is available"""
    return get_system_detector().has_pwd

def get_os_name():
    """Quick getter for OS display name"""
    return get_system_detector().get_os_display_name()

