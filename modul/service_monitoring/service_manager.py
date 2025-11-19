import os
import subprocess
import platform
import re
import json
import shutil
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ServiceManager:
    """Advanced service management class - works on all Linux distributions"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.distro = self._detect_distro()
        self.services_cache = {}
        self.last_update = None
        self.CACHE_TIMEOUT = 30  # 30 seconds cache
        
    def _detect_distro(self) -> str:
        """Detect Linux distribution"""
        try:
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    content = f.read()
                    if 'ubuntu' in content.lower():
                        return 'ubuntu'
                    elif 'debian' in content.lower():
                        return 'debian'
                    elif 'arch' in content.lower():
                        return 'arch'
                    elif 'fedora' in content.lower():
                        return 'fedora'
                    elif 'centos' in content.lower():
                        return 'centos'
        except:
            pass
        return 'unknown'
    
    def _run_command(self, command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """Safe command execution"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def _detect_service_category(self, name: str, description: str = "") -> str:
        """Intelligent service category detection"""
        name_lower = name.lower()
        desc_lower = description.lower()
        
        categories = {
            'Web Server': ['nginx', 'apache', 'httpd', 'www', 'lighttpd'],
            'Python Application': ['django', 'flask', 'gunicorn', 'uwsgi', 'python'],
            'PHP Application': ['php-fpm', 'php', 'apache2'],
            'Database': ['mysql', 'mariadb', 'postgresql', 'postgres', 'mongodb', 'redis'],
            'Cache Service': ['redis', 'memcached', 'varnish'],
            'System Service': ['systemd', 'init', 'cron', 'ssh', 'network'],
            'Network Service': ['network', 'networkmanager', 'dhcp', 'dns'],
            'Security': ['firewall', 'iptables', 'ufw', 'fail2ban'],
            'Docker': ['docker', 'containerd', 'dockerd'],
            'Monitoring': ['prometheus', 'grafana', 'zabbix', 'nagios'],
            'Other': []
        }
        
        for category, keywords in categories.items():
            if any(keyword in name_lower or keyword in desc_lower for keyword in keywords):
                return category
        
        return 'Other'
    
    def get_services(self, force_refresh: bool = False) -> List[Dict]:
        """Get all services - optimized with cache"""
        current_time = datetime.now()
        
        # Cache check
        if (not force_refresh and 
            self.last_update and 
            (current_time - self.last_update).seconds < self.CACHE_TIMEOUT and 
            self.services_cache):
            return self.services_cache
        
        services = []
        
        if self.system == "linux":
            services.extend(self._get_systemd_services())
        
        # Update cache
        self.services_cache = services
        self.last_update = current_time
        
        return services
    
    def _get_systemd_services(self) -> List[Dict]:
        """List systemd services"""
        services = []
        
        try:
            # List all services
            success, output, error = self._run_command(
                "systemctl list-unit-files --type=service --all --no-pager"
            )
            
            if not success:
                logger.error(f"Could not get service list: {error}")
                return services
            
            for line in output.split("\n"):
                # Parse service name and status
                match = re.match(r"^([\w\-@\.]+)\.service\s+(\w+)", line)
                if not match:
                    continue
                
                name = match.group(1)
                enabled_status = match.group(2)
                
                # Get service details
                service_info = self._get_service_info(name)
                service_info.update({
                    "name": name,
                    "enabled": enabled_status.lower() == "enabled",
                    "category": self._detect_service_category(name, service_info.get("description", "")),
                    "type": "systemd"
                })
                
                services.append(service_info)
            
            return services
            
        except Exception as e:
            logger.error(f"Error getting systemd services: {e}")
            return services
    
    def _get_service_info(self, name: str) -> Dict:
        """Get detailed information for a single service"""
        info = {
            "status": "inactive",
            "description": "",
            "loaded": False,
            "active": False,
            "uptime": "",
            "memory_usage": "0",
            "cpu_usage": "0",
            "pid": None
        }
        
        try:
            # Service status
            success, status_output, _ = self._run_command(f"systemctl is-active {name}")
            if success and status_output == "active":
                info["status"] = "active"
                info["active"] = True
            
            # Is service loaded
            success, loaded_output, _ = self._run_command(f"systemctl is-enabled {name}")
            if success:
                info["loaded"] = True
            
            # Detailed status information
            success, detailed_output, _ = self._run_command(f"systemctl status {name} --no-pager")
            if success:
                # Description
                desc_match = re.search(r"Description:\s*(.+)", detailed_output)
                if desc_match:
                    info["description"] = desc_match.group(1).strip()
                
                # PID
                pid_match = re.search(r"Main PID:\s*(\d+)", detailed_output)
                if pid_match:
                    info["pid"] = int(pid_match.group(1))
                
                # Uptime
                uptime_match = re.search(r"Active:\s*active\s*\((.+)\)", detailed_output)
                if uptime_match:
                    info["uptime"] = uptime_match.group(1).strip()
            
            # Resource usage (if active)
            if info["active"] and info["pid"]:
                self._get_resource_usage(info["pid"], info)
            
        except Exception as e:
            logger.error(f"Error getting service info ({name}): {e}")
        
        return info
    
    def _get_resource_usage(self, pid: int, info: Dict):
        """Get resource usage for PID"""
        try:
            # Memory usage
            success, mem_output, _ = self._run_command(f"ps -p {pid} -o %mem --no-headers")
            if success and mem_output:
                info["memory_usage"] = mem_output.strip()
            
            # CPU usage
            success, cpu_output, _ = self._run_command(f"ps -p {pid} -o %cpu --no-headers")
            if success and cpu_output:
                info["cpu_usage"] = cpu_output.strip()
                
        except Exception as e:
            logger.error(f"Error getting resource usage (PID {pid}): {e}")
    
    def control_service(self, name: str, action: str) -> Tuple[bool, str]:
        """Service control - safe"""
        valid_actions = ['start', 'stop', 'restart', 'enable', 'disable', 'reload']
        
        if action not in valid_actions:
            return False, f"Invalid action: {action}"
        
        try:
            # Run with sudo
            command = f"sudo systemctl {action} {name}"
            success, output, error = self._run_command(command, timeout=60)
            
            if success:
                # Clear cache
                self.last_update = None
                self.services_cache = {}
                
                action_texts = {
                    'start': 'started',
                    'stop': 'stopped',
                    'restart': 'restarted',
                    'enable': 'enabled',
                    'disable': 'disabled',
                    'reload': 'reloaded'
                }
                
                return True, f"{name} service {action_texts.get(action, action)}"
            else:
                return False, f"Operation failed: {error or output}"
                
        except Exception as e:
            logger.error(f"Error during service control ({name}, {action}): {e}")
            return False, str(e)
    
    
    def delete_service(self, name: str) -> Tuple[bool, str]:
        """Servis sil"""
        try:
            # Servisi durdur ve devre dışı bırak
            self.control_service(name, 'stop')
            self.control_service(name, 'disable')
            
            # Servis dosyasını bul ve sil
            success, unit_file, _ = self._run_command(f"systemctl show -p FragmentPath {name} | cut -d= -f2")
            
            if not success or not unit_file:
                return False, f"Servis dosyası bulunamadı: {name}"
            
            # Dosyayı sil
            success, output, error = self._run_command(f"sudo rm {unit_file}")
            if not success:
                return False, f"Dosya silinemedi: {error}"
            
            # Systemd'yi yenile
            self._run_command("sudo systemctl daemon-reload")
            
            # Cache'i temizle
            self.last_update = None
            self.services_cache = {}
            
            return True, f"{name} servisi başarıyla silindi"
            
        except Exception as e:
            logger.error(f"Servis silme hatası ({name}): {e}")
            return False, str(e)
    
    def get_service_logs(self, name: str, lines: int = 50) -> List[str]:
        """Servis loglarını al"""
        try:
            success, output, error = self._run_command(f"journalctl -u {name} -n {lines} --no-pager")
            if success:
                return output.split('\n')
            return []
        except Exception as e:
            logger.error(f"Log alınırken hata ({name}): {e}")
            return []
    
    def get_service_details(self, name: str) -> Dict:
        """Detaylı servis bilgisi"""
        try:
            details = {
                "name": name,
                "status": "inactive",
                "description": "",
                "loaded": False,
                "enabled": False,
                "active": False,
                "uptime": "",
                "memory_usage": "0",
                "cpu_usage": "0",
                "pid": None,
                "unit_file": "",
                "dependencies": [],
                "logs": [],
                "properties": {}
            }
            
            # Temel durum
            success, status, _ = self._run_command(f"systemctl is-active {name}")
            if success and status == "active":
                details["active"] = True
                details["status"] = "active"
            
            success, enabled, _ = self._run_command(f"systemctl is-enabled {name}")
            if success:
                details["enabled"] = enabled == "enabled"
                details["loaded"] = True
            
            # Detaylı durum
            success, status_output, _ = self._run_command(f"systemctl status {name} --no-pager")
            if success:
                # Açıklama
                desc_match = re.search(r"Description:\s*(.+)", status_output)
                if desc_match:
                    details["description"] = desc_match.group(1).strip()
                
                # PID
                pid_match = re.search(r"Main PID:\s*(\d+)", status_output)
                if pid_match:
                    details["pid"] = int(pid_match.group(1))
                
                # Uptime
                uptime_match = re.search(r"Active:\s*active\s*\((.+)\)", status_output)
                if uptime_match:
                    details["uptime"] = uptime_match.group(1).strip()
            
            # Unit file
            success, unit_content, _ = self._run_command(f"systemctl cat {name}")
            if success:
                details["unit_file"] = unit_content
            
            # Dependencies
            success, deps_output, _ = self._run_command(f"systemctl list-dependencies {name} --no-pager")
            if success:
                details["dependencies"] = [
                    dep.strip('└─ ').strip('├─ ').strip()
                    for dep in deps_output.split('\n')[1:]
                    if dep.strip()
                ]
            
            # Properties
            success, props_output, _ = self._run_command(f"systemctl show {name}")
            if success:
                for line in props_output.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        details["properties"][key] = value
            
            # Logs
            details["logs"] = self.get_service_logs(name, 20)
            
            return details
            
        except Exception as e:
            logger.error(f"Servis detayları alınırken hata ({name}): {e}")
            return {"name": name, "error": str(e)}

# Global instance
service_manager = ServiceManager()
