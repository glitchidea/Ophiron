"""
System Information Utilities
Sistem bilgilerini toplama ve işleme fonksiyonları
"""

import psutil
import platform
import socket
import subprocess
import os
import logging
from datetime import datetime
import time

# Optional imports based on platform
try:
    import pwd
    PWD_AVAILABLE = True
except ImportError:
    PWD_AVAILABLE = False
    pwd = None

try:
    import netifaces
    NETIFACES_AVAILABLE = True
except ImportError:
    NETIFACES_AVAILABLE = False
    logging.warning("netifaces module not available. Some network features will be limited.")

# Windows-specific imports
try:
    import win32net
    import win32netcon
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    win32net = None
    win32netcon = None

# Import our system detector
from .system_detector import get_system_detector

logger = logging.getLogger(__name__)


class SystemInfo:
    """Sistem bilgileri toplama sınıfı"""
    
    def __init__(self):
        """SystemInfo sınıfını başlat"""
        self.logger = logger
        self.detector = get_system_detector()
        self.is_windows = self.detector.is_windows
        self.is_linux = self.detector.is_linux
        self.is_macos = self.detector.is_macos
    
    def get_cpu_info(self):
        """CPU bilgilerini al"""
        try:
            model = platform.processor()
            
            # Linux için model name'i /proc/cpuinfo'dan al
            if platform.system() == 'Linux':
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        for line in f:
                            if 'model name' in line:
                                model = line.split(':')[1].strip()
                                break
                except:
                    pass
            
            cpu_freq = psutil.cpu_freq()
            
            return {
                'model': model or 'Unknown',
                'architecture': platform.machine(),
                'cores': psutil.cpu_count(logical=False) or psutil.cpu_count(),
                'logical_cores': psutil.cpu_count(),
                'frequency': round(cpu_freq.current, 2) if cpu_freq else 0,
                'max_frequency': round(cpu_freq.max, 2) if cpu_freq and cpu_freq.max else 0,
                'usage_percent': round(psutil.cpu_percent(interval=1), 1),
                'per_cpu_percent': [round(p, 1) for p in psutil.cpu_percent(interval=0.5, percpu=True)]
            }
        except Exception as e:
            self.logger.error(f"CPU bilgileri alınırken hata: {e}")
            return {
                'model': 'Unknown',
                'architecture': platform.machine(),
                'cores': psutil.cpu_count() or 0,
                'logical_cores': psutil.cpu_count() or 0,
                'frequency': 0,
                'max_frequency': 0,
                'usage_percent': 0,
                'per_cpu_percent': []
            }
    
    def get_memory_info(self):
        """Bellek bilgilerini al"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'total': round(memory.total / (1024**3), 2),
                'available': round(memory.available / (1024**3), 2),
                'used': round(memory.used / (1024**3), 2),
                'free': round(memory.free / (1024**3), 2),
                'percent': round(memory.percent, 1),
                'swap_total': round(swap.total / (1024**3), 2),
                'swap_used': round(swap.used / (1024**3), 2),
                'swap_free': round(swap.free / (1024**3), 2),
                'swap_percent': round(swap.percent, 1)
            }
        except Exception as e:
            self.logger.error(f"Bellek bilgileri alınırken hata: {e}")
            return {
                'total': 0, 'available': 0, 'used': 0, 'free': 0, 'percent': 0,
                'swap_total': 0, 'swap_used': 0, 'swap_free': 0, 'swap_percent': 0
            }
    
    def get_disk_info(self):
        """Disk bilgilerini al"""
        try:
            disk_info = []
            total_space = 0
            used_space = 0
            
            for partition in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    total_space += usage.total
                    used_space += usage.used
                    
                    disk_info.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': round(usage.total / (1024**3), 1),
                        'used': round(usage.used / (1024**3), 1),
                        'free': round(usage.free / (1024**3), 1),
                        'percent': round(usage.percent, 1)
                    })
                except (PermissionError, OSError):
                    continue
            
            return {
                'partitions': disk_info,
                'total_space': round(total_space / (1024**3), 1),
                'used_space': round(used_space / (1024**3), 1),
                'free_space': round((total_space - used_space) / (1024**3), 1),
                'total_percent': round((used_space / total_space * 100), 1) if total_space > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Disk bilgileri alınırken hata: {e}")
            return {
                'partitions': [],
                'total_space': 0,
                'used_space': 0,
                'free_space': 0,
                'total_percent': 0
            }
    
    def get_network_info(self):
        """Ağ bilgilerini al"""
        try:
            network_info = {
                'interfaces': [],
                'dns': {},
                'routes': []
            }
            
            # Ağ arayüzleri bilgilerini al
            if NETIFACES_AVAILABLE:
                for interface in netifaces.interfaces():
                    try:
                        addrs = netifaces.ifaddresses(interface)
                        if netifaces.AF_INET in addrs:
                            for addr in addrs[netifaces.AF_INET]:
                                net_stats = psutil.net_io_counters(pernic=True).get(interface, None)
                                network_info['interfaces'].append({
                                    'name': interface,
                                    'ip': addr['addr'],
                                    'netmask': addr.get('netmask', 'N/A'),
                                    'bytes_sent': net_stats.bytes_sent if net_stats else 0,
                                    'bytes_recv': net_stats.bytes_recv if net_stats else 0
                                })
                    except:
                        continue
            else:
                # Fallback: psutil kullan
                net_io = psutil.net_io_counters(pernic=True)
                for interface, stats in net_io.items():
                    network_info['interfaces'].append({
                        'name': interface,
                        'ip': 'N/A',
                        'netmask': 'N/A',
                        'bytes_sent': stats.bytes_sent,
                        'bytes_recv': stats.bytes_recv
                    })
            
            # DNS bilgilerini al
            try:
                if os.path.exists('/etc/resolv.conf'):
                    with open('/etc/resolv.conf', 'r') as f:
                        dns_content = f.readlines()
                        network_info['dns'] = {
                            'nameserver': next((line.split()[1] for line in dns_content if line.startswith('nameserver')), 'N/A'),
                            'search': next((line.split()[1] for line in dns_content if line.startswith('search')), 'N/A'),
                            'generator': 'NetworkManager'
                        }
                else:
                    network_info['dns'] = {'nameserver': 'N/A', 'search': 'N/A', 'generator': 'N/A'}
            except:
                network_info['dns'] = {'nameserver': 'N/A', 'search': 'N/A', 'generator': 'N/A'}
            
            # Routing bilgilerini al
            try:
                routing_output = subprocess.getoutput("ip route")
                for line in routing_output.split('\n'):
                    if line.strip():
                        route_info = self._parse_route_info(line)
                        network_info['routes'].append(route_info)
            except:
                pass
            
            return network_info
        except Exception as e:
            self.logger.error(f"Ağ bilgileri alınırken hata: {e}")
            return {
                'interfaces': [],
                'dns': {'nameserver': 'N/A', 'search': 'N/A', 'generator': 'N/A'},
                'routes': []
            }
    
    def _parse_route_info(self, route_line):
        """Route bilgisini parse et"""
        route_info = {}
        parts = route_line.split()
        
        # Rota tipini belirle
        if route_line.startswith('default'):
            route_info['type'] = 'default'
        elif 'via' in parts:
            route_info['type'] = 'via'
        else:
            route_info['type'] = 'direct'
        
        # Detayları parse et
        route_info['interface'] = parts[parts.index('dev') + 1] if 'dev' in parts else 'N/A'
        route_info['protocol'] = parts[parts.index('proto') + 1] if 'proto' in parts else 'N/A'
        route_info['details'] = route_line
        
        return route_info
    
    def get_os_info(self):
        """İşletim sistemi bilgilerini al (System Detector ile zenginleştirilmiş)"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            # Uptime formatla
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m"
            
            # System Detector bilgilerini ekle
            detector_info = self.detector.get_system_info()
            
            return {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'node': socket.gethostname(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'uptime': uptime_str,
                'boot_time': boot_time.strftime("%Y-%m-%d %H:%M:%S"),
                'timezone': time.strftime('%z'),
                # System Detector eklentileri
                'os_display_name': detector_info['os_display_name'],
                'distro_family': detector_info['distro_family'],
                'package_manager': detector_info['package_manager'],
                'platform_type': 'Windows' if self.is_windows else 'macOS' if self.is_macos else 'Linux'
            }
        except Exception as e:
            self.logger.error(f"İşletim sistemi bilgileri alınırken hata: {e}")
            return {
                'system': platform.system(),
                'release': 'Unknown',
                'version': 'Unknown',
                'node': socket.gethostname(),
                'machine': platform.machine(),
                'processor': 'Unknown',
                'uptime': 'Unknown',
                'boot_time': 'Unknown',
                'timezone': time.strftime('%z'),
                'os_display_name': 'Unknown',
                'distro_family': 'unknown',
                'package_manager': 'unknown',
                'platform_type': 'Unknown'
            }
    
    def get_system_users(self):
        """Sistem kullanıcılarını al (Platform-specific)"""
        users = []
        
        # Windows için
        if self.is_windows:
            users = self._get_windows_users()
        # Linux/Unix için (pwd kullanılabilir)
        elif self.is_linux and PWD_AVAILABLE and pwd:
            users = self._get_unix_users()
        # macOS için
        elif self.is_macos and PWD_AVAILABLE and pwd:
            users = self._get_unix_users()
        else:
            self.logger.warning("User information not available for this platform")
            
        return users
    
    def _get_windows_users(self):
        """Windows kullanıcılarını al"""
        users = []
        
        try:
            # Method 1: win32net (daha detaylı bilgi)
            if WIN32_AVAILABLE and win32net:
                try:
                    resume = 0
                    while True:
                        (user_list, total, resume) = win32net.NetUserEnum(
                            None,  # Local computer
                            3,     # Level 3 (detailed info)
                            win32netcon.FILTER_NORMAL_ACCOUNT,
                            resume
                        )
                        
                        for user_info in user_list:
                            # Filter out system accounts
                            username = user_info['name']
                            if username.lower() not in ['defaultaccount', 'guest', 'wdagutilityaccount']:
                                users.append({
                                    'username': username,
                                    'uid': user_info.get('user_id', 'N/A'),
                                    'gid': 'N/A',  # Windows doesn't have GID concept like Unix
                                    'home': user_info.get('home_dir', 'N/A') or 'N/A',
                                    'shell': 'cmd.exe',  # Windows default
                                    'full_name': user_info.get('full_name', ''),
                                    'comment': user_info.get('comment', '')
                                })
                        
                        if resume == 0:
                            break
                    
                    return users
                except Exception as e:
                    self.logger.debug(f"win32net method failed: {e}")
            
            # Method 2: WMI via subprocess (fallback)
            try:
                result = subprocess.run(
                    ['wmic', 'useraccount', 'get', 'name,sid,fullname', '/format:csv'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[2:]:  # Skip header lines
                        if line.strip():
                            parts = line.split(',')
                            if len(parts) >= 3:
                                username = parts[2].strip()
                                full_name = parts[1].strip() if len(parts) > 1 else ''
                                sid = parts[3].strip() if len(parts) > 3 else ''
                                
                                if username and username.lower() not in ['defaultaccount', 'guest', 'wdagutilityaccount']:
                                    users.append({
                                        'username': username,
                                        'uid': sid,
                                        'gid': 'N/A',
                                        'home': f'C:\\Users\\{username}',
                                        'shell': 'cmd.exe',
                                        'full_name': full_name
                                    })
                    return users
            except Exception as e:
                self.logger.debug(f"WMI method failed: {e}")
            
            # Method 3: Simple net user command (most basic fallback)
            try:
                result = subprocess.run(['net', 'user'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    output = result.stdout
                    lines = output.split('\n')
                    
                    # Find the section with usernames
                    user_section_started = False
                    for line in lines:
                        if '-----' in line:
                            user_section_started = True
                            continue
                        
                        if user_section_started:
                            if line.strip() and 'The command completed successfully' not in line:
                                # Extract usernames (they're space-separated)
                                usernames = line.split()
                                for username in usernames:
                                    username = username.strip()
                                    if username and username.lower() not in ['defaultaccount', 'guest', 'wdagutilityaccount']:
                                        users.append({
                                            'username': username,
                                            'uid': 'N/A',
                                            'gid': 'N/A',
                                            'home': f'C:\\Users\\{username}',
                                            'shell': 'cmd.exe'
                                        })
                            else:
                                break
                    
                    return users
            except Exception as e:
                self.logger.debug(f"net user method failed: {e}")
            
        except Exception as e:
            self.logger.error(f"Windows kullanıcı bilgileri alınırken hata: {e}")
        
        return users
    
    def _get_unix_users(self):
        """Unix/Linux/macOS kullanıcılarını al"""
        users = []
        
        try:
            if not pwd:
                return users
            
            for user in pwd.getpwall():
                # Filter criteria based on platform
                if self.is_linux:
                    # Linux: UID >= 1000 and not nologin shell
                    if user.pw_uid >= 1000 and user.pw_shell not in ['/sbin/nologin', '/usr/sbin/nologin', '/bin/false']:
                        users.append({
                            'username': user.pw_name,
                            'uid': user.pw_uid,
                            'gid': user.pw_gid,
                            'home': user.pw_dir,
                            'shell': user.pw_shell
                        })
                elif self.is_macos:
                    # macOS: UID >= 500 (macOS uses different UID ranges)
                    if user.pw_uid >= 500 and user.pw_shell not in ['/usr/bin/false']:
                        users.append({
                            'username': user.pw_name,
                            'uid': user.pw_uid,
                            'gid': user.pw_gid,
                            'home': user.pw_dir,
                            'shell': user.pw_shell
                        })
                else:
                    # Generic Unix
                    if user.pw_uid >= 1000:
                        users.append({
                            'username': user.pw_name,
                            'uid': user.pw_uid,
                            'gid': user.pw_gid,
                            'home': user.pw_dir,
                            'shell': user.pw_shell
                        })
        except Exception as e:
            self.logger.error(f"Unix kullanıcı bilgileri alınırken hata: {e}")
        
        return users
    
    def get_security_info(self):
        """Güvenlik bilgilerini al (Platform-specific)"""
        security_info = {
            'active_users': [],
            'active_connections': []
        }
        
        try:
            # Aktif kullanıcılar
            if self.is_windows:
                security_info['active_users'] = self._parse_windows_active_users()
            else:
                security_info['active_users'] = self._parse_unix_active_users()
            
            # Aktif bağlantılar
            if self.is_windows:
                security_info['active_connections'] = self._parse_windows_active_connections()
            else:
                security_info['active_connections'] = self._parse_unix_active_connections()
            
            return security_info
        except Exception as e:
            self.logger.error(f"Güvenlik bilgileri alınırken hata: {e}")
            return security_info
    
    def _parse_windows_active_users(self):
        """Windows aktif kullanıcıları parse et"""
        try:
            result = subprocess.run(['query', 'user'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return self._parse_windows_user_output(result.stdout)
            else:
                # Fallback to qwinsta
                result = subprocess.run(['qwinsta'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return self._parse_windows_user_output(result.stdout)
                return []
        except Exception as e:
            self.logger.debug(f"Windows active users error: {e}")
            return []
    
    def _parse_windows_user_output(self, output):
        """Windows user output'unu parse et"""
        users = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if 'console' in line.lower() or 'rdp' in line.lower() or 'services' in line.lower():
                parts = line.split()
                if len(parts) >= 3:
                    users.append({
                        'username': parts[1] if len(parts) > 1 else 'Unknown',
                        'session': parts[0] if parts[0] else 'Unknown',
                        'state': parts[2] if len(parts) > 2 else 'Unknown'
                    })
        
        return users
    
    def _parse_unix_active_users(self):
        """Unix/Linux aktif kullanıcıları parse et"""
        try:
            result = subprocess.run(['who'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return self._parse_unix_user_output(result.stdout)
            return []
        except Exception as e:
            self.logger.debug(f"Unix active users error: {e}")
            return []
    
    def _parse_unix_user_output(self, output):
        """Unix user output'unu parse et"""
        users = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    users.append({
                        'username': parts[0],
                        'session': parts[1] if len(parts) > 1 else 'Unknown',
                        'state': 'Active'
                    })
        
        return users
    
    def _parse_windows_active_connections(self):
        """Windows aktif bağlantıları parse et"""
        try:
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return self._parse_windows_connection_output(result.stdout)
            return []
        except Exception as e:
            self.logger.debug(f"Windows active connections error: {e}")
            return []
    
    def _parse_windows_connection_output(self, output):
        """Windows connection output'unu parse et"""
        connections = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if 'LISTENING' in line or 'ESTABLISHED' in line:
                parts = line.split()
                if len(parts) >= 4:
                    connections.append({
                        'type': 'TCP',
                        'details': f"{parts[1]} -> {parts[2]}",
                        'status': parts[3] if len(parts) > 3 else 'Unknown'
                    })
        
        return connections[:20]  # Limit to 20 connections
    
    def _parse_unix_active_connections(self):
        """Unix/Linux aktif bağlantıları parse et"""
        try:
            result = subprocess.run(['netstat', '-tuln'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return self._parse_unix_connection_output(result.stdout)
            return []
        except Exception as e:
            self.logger.debug(f"Unix active connections error: {e}")
            return []
    
    def _parse_unix_connection_output(self, output):
        """Unix connection output'unu parse et"""
        connections = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if 'LISTEN' in line or 'ESTABLISHED' in line:
                parts = line.split()
                if len(parts) >= 4:
                    connections.append({
                        'type': parts[0] if parts[0] else 'Unknown',
                        'details': f"{parts[3]} -> {parts[4] if len(parts) > 4 else 'Unknown'}",
                        'status': 'Active'
                    })
        
        return connections[:20]  # Limit to 20 connections
    
    
    def get_all_system_info(self):
        """Tüm sistem bilgilerini topla"""
        try:
            return {
                'cpu': self.get_cpu_info(),
                'memory': self.get_memory_info(),
                'disk': self.get_disk_info(),
                'network': self.get_network_info(),
                'os': self.get_os_info(),
                'users': self.get_system_users(),
                'security': self.get_security_info()
            }
        except Exception as e:
            self.logger.error(f"Sistem bilgileri toplarken hata: {e}")
            return {}


# Global instance
system_info_collector = SystemInfo()
