import psutil
import os
import platform
import subprocess
import json
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import socket
import threading

logger = logging.getLogger(__name__)


class ProcessCollector:
    """
    Genel süreç toplama sınıfı - platform bağımsız
    """
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.collector = self._get_platform_collector()
    
    def _get_platform_collector(self):
        """Platform'a göre uygun collector'ı döndürür"""
        if self.platform == 'linux':
            return LinuxProcessCollector()
        else:
            raise NotImplementedError(f"Platform {self.platform} not supported")
    
    def collect_processes(self, **kwargs):
        """Süreçleri toplar"""
        return self.collector.collect_processes(**kwargs)
    
    def collect_connections(self, processes_data):
        """Bağlantıları toplar"""
        return self.collector.collect_connections(processes_data)
    
    def get_process_details(self, pid):
        """Süreç detaylarını alır"""
        return self.collector.get_process_details(pid)
    
    def get_process_connections(self, pid):
        """Süreç bağlantılarını alır"""
        return self.collector.get_process_connections(pid)


class LinuxProcessCollector:
    """
    Linux sistemler için süreç toplama sınıfı
    Tüm Linux dağıtımlarında çalışacak şekilde tasarlanmış
    """
    
    def __init__(self):
        self.system_info = self._get_system_info()
    
    def _get_system_info(self):
        """Sistem bilgilerini alır"""
        try:
            return {
                'os_name': platform.system(),
                'os_version': platform.version(),
                'hostname': platform.node(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'memory_total': psutil.virtual_memory().total,
                'boot_time': psutil.boot_time(),
                'uptime': time.time() - psutil.boot_time()
            }
        except Exception as e:
            logger.error(f"System info collection error: {str(e)}")
            return {}
    
    def collect_processes(self, limit=100, status_filter='', user_filter='', search_query=''):
        """
        Sistem süreçlerini toplar
        Tüm Linux dağıtımlarında çalışacak şekilde tasarlanmış
        """
        try:
            processes = []
            collected = 0
            
            # Süreçleri topla
            for proc in psutil.process_iter(['pid', 'name', 'status', 'username', 'cpu_percent', 
                                           'memory_percent', 'memory_info', 'num_threads', 
                                           'create_time', 'ppid', 'cmdline', 'cwd']):
                try:
                    if collected >= limit:
                        break
                    
                    info = proc.info
                    
                    # Filtreleri uygula
                    if status_filter and info['status'] != status_filter:
                        continue
                    if user_filter and user_filter not in info.get('username', ''):
                        continue
                    if search_query and search_query.lower() not in info.get('name', '').lower():
                        continue
                    
                    # Bellek bilgilerini al
                    memory_info = info.get('memory_info')
                    memory_rss = memory_info.rss if memory_info else 0
                    memory_vms = memory_info.vms if memory_info else 0
                    
                    # Süreç verilerini hazırla
                    process_data = {
                        'pid': info['pid'],
                        'name': info['name'],
                        'status': info['status'],
                        'user': info.get('username', 'unknown'),
                        'cpu_percent': info.get('cpu_percent', 0.0),
                        'memory_percent': info.get('memory_percent', 0.0),
                        'memory_rss': memory_rss,
                        'memory_vms': memory_vms,
                        'num_threads': info.get('num_threads', 1),
                        'create_time': datetime.fromtimestamp(info['create_time']).isoformat(),
                        'parent_pid': info.get('ppid'),
                        'command_line': ' '.join(info.get('cmdline', [])),
                        'working_directory': info.get('cwd', ''),
                        'x': 0.0,  # Graph pozisyonu
                        'y': 0.0,  # Graph pozisyonu
                        'size': self._calculate_node_size(info),
                        'color': self._get_node_color(info)
                    }
                    
                    processes.append(process_data)
                    collected += 1
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    logger.warning(f"Process collection error for PID {proc.pid}: {str(e)}")
                    continue
            
            return processes
            
        except Exception as e:
            logger.error(f"Process collection error: {str(e)}")
            return []
    
    def _calculate_node_size(self, process_info):
        """Düğüm boyutunu hesaplar"""
        cpu_percent = process_info.get('cpu_percent', 0.0)
        memory_percent = process_info.get('memory_percent', 0.0)
        
        # CPU ve bellek kullanımına göre boyut hesapla
        base_size = 1.0
        cpu_factor = min(cpu_percent / 10.0, 3.0)  # Max 3x
        memory_factor = min(memory_percent / 5.0, 3.0)  # Max 3x
        
        return base_size + (cpu_factor + memory_factor) / 2
    
    def _get_node_color(self, process_info):
        """Düğüm rengini belirler"""
        status = process_info.get('status', 'R')
        
        status_colors = {
            'R': '#28a745',  # Green - Running
            'S': '#17a2b8',  # Cyan - Sleeping
            'D': '#ffc107',  # Yellow - Disk Sleep
            'Z': '#dc3545',  # Red - Zombie
            'T': '#6c757d',  # Gray - Stopped
            't': '#6c757d',  # Gray - Tracing Stop
            'X': '#343a40',  # Dark - Dead
            'x': '#343a40',  # Dark - Dead
            'K': '#fd7e14',  # Orange - Wakekill
            'W': '#20c997',  # Teal - Waking
            'P': '#6f42c1',  # Purple - Parked
        }
        
        return status_colors.get(status, '#6c757d')
    
    def collect_connections(self, processes_data):
        """
        Süreçler arası bağlantıları toplar
        """
        try:
            connections = []
            process_pids = {p['pid']: p for p in processes_data}
            
            for process_data in processes_data:
                pid = process_data['pid']
                parent_pid = process_data.get('parent_pid')
                
                # Ebeveyn-çocuk bağlantısı
                if parent_pid and parent_pid in process_pids:
                    connections.append({
                        'source': parent_pid,
                        'target': pid,
                        'type': 'parent_child',
                        'weight': 1.0,
                        'color': '#007bff',
                        'width': 1.0
                    })
                
                # Ağ bağlantıları
                network_connections = self._get_network_connections(pid)
                for conn in network_connections:
                    if conn['remote_pid'] in process_pids:
                        connections.append({
                            'source': pid,
                            'target': conn['remote_pid'],
                            'type': 'network',
                            'weight': conn.get('weight', 1.0),
                            'color': '#28a745',
                            'width': 1.0,
                            'metadata': conn
                        })
            
            return connections
            
        except Exception as e:
            logger.error(f"Connection collection error: {str(e)}")
            return []
    
    def _get_network_connections(self, pid):
        """Sürecin ağ bağlantılarını alır"""
        try:
            process = psutil.Process(pid)
            connections = process.connections()
            
            network_conns = []
            for conn in connections:
                if conn.raddr and conn.raddr.port:
                    # Uzak port bilgisini kullanarak süreç bulmaya çalış
                    remote_pid = self._find_process_by_port(conn.raddr.port)
                    if remote_pid:
                        network_conns.append({
                            'remote_pid': remote_pid,
                            'local_addr': f"{conn.laddr.ip}:{conn.laddr.port}",
                            'remote_addr': f"{conn.raddr.ip}:{conn.raddr.port}",
                            'status': conn.status,
                            'weight': 1.0
                        })
            
            return network_conns
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []
        except Exception as e:
            logger.warning(f"Network connections error for PID {pid}: {str(e)}")
            return []
    
    def _find_process_by_port(self, port):
        """Port kullanan süreci bulur"""
        try:
            for proc in psutil.process_iter(['pid', 'connections']):
                try:
                    connections = proc.connections()
                    for conn in connections:
                        if conn.laddr and conn.laddr.port == port:
                            return proc.pid
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.warning(f"Port process finding error: {str(e)}")
        
        return None
    
    def get_process_details(self, pid):
        """Belirli bir sürecin detay bilgilerini alır"""
        try:
            process = psutil.Process(pid)
            
            # Temel bilgiler
            info = {
                'pid': process.pid,
                'name': process.name(),
                'status': process.status(),
                'username': process.username(),
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'memory_info': {
                    'rss': process.memory_info().rss,
                    'vms': process.memory_info().vms,
                    'shared': process.memory_info().shared if hasattr(process.memory_info(), 'shared') else 0,
                    'text': process.memory_info().text if hasattr(process.memory_info(), 'text') else 0,
                    'data': process.memory_info().data if hasattr(process.memory_info(), 'data') else 0,
                },
                'num_threads': process.num_threads(),
                'create_time': datetime.fromtimestamp(process.create_time()).isoformat(),
                'parent_pid': process.ppid(),
                'command_line': ' '.join(process.cmdline()),
                'working_directory': process.cwd(),
                'environment': dict(process.environ()),
                'io_counters': {
                    'read_count': process.io_counters().read_count if process.io_counters() else 0,
                    'write_count': process.io_counters().write_count if process.io_counters() else 0,
                    'read_bytes': process.io_counters().read_bytes if process.io_counters() else 0,
                    'write_bytes': process.io_counters().write_bytes if process.io_counters() else 0,
                },
                'connections': len(process.connections()),
                'open_files': len(process.open_files()),
                'children': [child.pid for child in process.children(recursive=False)],
                'nice': process.nice(),
                'ionice': process.ionice() if hasattr(process, 'ionice') else None,
            }
            
            # Linux özel bilgiler
            try:
                info.update({
                    'num_fds': process.num_fds(),
                    'cpu_affinity': process.cpu_affinity(),
                    'memory_maps': self._get_memory_maps(pid),
                    'threads': self._get_thread_info(pid),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                pass
            
            return info
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Process details error for PID {pid}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Process details error for PID {pid}: {str(e)}")
            return None
    
    def _get_memory_maps(self, pid):
        """Sürecin bellek haritasını alır"""
        try:
            process = psutil.Process(pid)
            maps = process.memory_maps()
            return [{
                'path': mmap.path,
                'rss': mmap.rss,
                'size': mmap.size,
                'pss': mmap.pss if hasattr(mmap, 'pss') else 0,
                'shared_clean': mmap.shared_clean if hasattr(mmap, 'shared_clean') else 0,
                'shared_dirty': mmap.shared_dirty if hasattr(mmap, 'shared_dirty') else 0,
                'private_clean': mmap.private_clean if hasattr(mmap, 'private_clean') else 0,
                'private_dirty': mmap.private_dirty if hasattr(mmap, 'private_dirty') else 0,
                'referenced': mmap.referenced if hasattr(mmap, 'referenced') else 0,
                'anonymous': mmap.anonymous if hasattr(mmap, 'anonymous') else 0,
                'swap': mmap.swap if hasattr(mmap, 'swap') else 0,
            } for mmap in maps]
        except Exception as e:
            logger.warning(f"Memory maps error for PID {pid}: {str(e)}")
            return []
    
    def _get_thread_info(self, pid):
        """Sürecin thread bilgilerini alır"""
        try:
            process = psutil.Process(pid)
            threads = process.threads()
            return [{
                'id': thread.id,
                'user_time': thread.user_time,
                'system_time': thread.system_time,
            } for thread in threads]
        except Exception as e:
            logger.warning(f"Thread info error for PID {pid}: {str(e)}")
            return []
    
    def get_process_connections(self, pid):
        """Sürecin bağlantılarını alır"""
        try:
            process = psutil.Process(pid)
            connections = process.connections()
            
            conn_data = []
            for conn in connections:
                conn_info = {
                    'fd': conn.fd,
                    'family': conn.family.name if conn.family else None,
                    'type': conn.type.name if conn.type else None,
                    'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                    'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                    'status': conn.status,
                    'pid': conn.pid if hasattr(conn, 'pid') else None,
                }
                conn_data.append(conn_info)
            
            return conn_data
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Process connections error for PID {pid}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Process connections error for PID {pid}: {str(e)}")
            return []
    
    def get_system_info(self):
        """Sistem bilgilerini döndürür"""
        return self.system_info


class SystemInfoCollector:
    """
    Sistem bilgilerini toplama sınıfı
    """
    
    def __init__(self):
        self.cached_info = None
        self.cache_time = 0
        self.cache_duration = 5  # 5 saniye cache
    
    def get_system_info(self):
        """Sistem bilgilerini alır"""
        current_time = time.time()
        
        if self.cached_info and (current_time - self.cache_time) < self.cache_duration:
            return self.cached_info
        
        try:
            info = {
                'os_name': platform.system(),
                'os_version': platform.version(),
                'hostname': platform.node(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'memory_used': psutil.virtual_memory().used,
                'memory_percent': psutil.virtual_memory().percent,
                'boot_time': psutil.boot_time(),
                'uptime': time.time() - psutil.boot_time(),
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
                'disk_usage': self._get_disk_usage(),
                'network_info': self._get_network_info(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self.cached_info = info
            self.cache_time = current_time
            
            return info
            
        except Exception as e:
            logger.error(f"System info collection error: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_system_metrics(self):
        """Sistem metriklerini alır"""
        try:
            # CPU bilgileri
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Bellek bilgileri
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk bilgileri
            disk = psutil.disk_usage('/')
            
            # Ağ bilgileri
            network = psutil.net_io_counters()
            
            # Yük ortalaması
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            
            metrics = {
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'cpu_frequency': {
                    'current': cpu_freq.current if cpu_freq else 0,
                    'min': cpu_freq.min if cpu_freq else 0,
                    'max': cpu_freq.max if cpu_freq else 0,
                },
                'memory_percent': memory.percent,
                'memory_used': memory.used,
                'memory_available': memory.available,
                'memory_total': memory.total,
                'swap_percent': swap.percent,
                'swap_used': swap.used,
                'swap_total': swap.total,
                'disk_percent': disk.percent,
                'disk_used': disk.used,
                'disk_free': disk.free,
                'disk_total': disk.total,
                'load_avg_1min': load_avg[0],
                'load_avg_5min': load_avg[1],
                'load_avg_15min': load_avg[2],
                'network_bytes_sent': network.bytes_sent if network else 0,
                'network_bytes_recv': network.bytes_recv if network else 0,
                'network_packets_sent': network.packets_sent if network else 0,
                'network_packets_recv': network.packets_recv if network else 0,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"System metrics collection error: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _get_disk_usage(self):
        """Disk kullanım bilgilerini alır"""
        try:
            disk_info = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100 if usage.total > 0 else 0
                    })
                except PermissionError:
                    continue
            return disk_info
        except Exception as e:
            logger.warning(f"Disk usage collection error: {str(e)}")
            return []
    
    def _get_network_info(self):
        """Ağ bilgilerini alır"""
        try:
            network_info = []
            for interface, addrs in psutil.net_if_addrs().items():
                interface_info = {
                    'interface': interface,
                    'addresses': []
                }
                
                for addr in addrs:
                    interface_info['addresses'].append({
                        'family': addr.family.name,
                        'address': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast,
                    })
                
                network_info.append(interface_info)
            
            return network_info
        except Exception as e:
            logger.warning(f"Network info collection error: {str(e)}")
            return []


class ProcessMonitor:
    """
    Süreç izleme sınıfı - gerçek zamanlı izleme
    """
    
    def __init__(self, callback=None):
        self.callback = callback
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval=5):
        """İzlemeyi başlatır"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """İzlemeyi durdurur"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
    
    def _monitor_loop(self, interval):
        """İzleme döngüsü"""
        collector = LinuxProcessCollector()
        
        while self.monitoring:
            try:
                # Süreçleri topla
                processes = collector.collect_processes(limit=200)
                
                # Sistem metriklerini al
                system_metrics = SystemInfoCollector().get_system_metrics()
                
                # Callback'i çağır
                if self.callback:
                    self.callback({
                        'processes': processes,
                        'system_metrics': system_metrics,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {str(e)}")
                time.sleep(interval)







