"""
Process Monitor Utilities
Helper functions for monitoring and managing network processes
"""

import psutil
import socket
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class ProcessMonitor:
    """Class for monitoring and managing system processes"""
    
    def __init__(self):
        self.process_cache = {}
    
    def get_all_processes(self):
        """Get all system processes"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'status', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                pinfo['cpu_percent'] = proc.cpu_percent(interval=0.1)
                pinfo['memory_percent'] = proc.memory_percent()
                processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return sorted(processes, key=lambda x: x.get('cpu_percent', 0), reverse=True)
    
    def get_process_name(self, pid):
        """Get process name"""
        try:
            process = psutil.Process(pid)
            return process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
    
    def get_process_connections(self, pid):
        """Get process connections"""
        try:
            process = psutil.Process(pid)
            return process.connections()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return []
    
    def get_process_details(self, pid):
        """Get detailed process information"""
        try:
            if pid in self.process_cache:
                return self.process_cache[pid]
            
            process = psutil.Process(pid)
            with process.oneshot():
                memory_info = process.memory_info()
                memory_percent = process.memory_percent()
                cpu_percent = process.cpu_percent(interval=0.1)
                
                details = {
                    'pid': pid,
                    'name': process.name(),
                    'status': process.status(),
                    'username': process.username(),
                    'nice': process.nice(),
                    'threads': process.num_threads(),
                    'memory_info': {
                        'rss': memory_info.rss,
                        'vms': memory_info.vms,
                        'shared': getattr(memory_info, 'shared', 0),
                        'text': getattr(memory_info, 'text', 0),
                        'data': getattr(memory_info, 'data', 0)
                    },
                    'memory_percent': memory_percent,
                    'cpu_percent': cpu_percent,
                    'create_time': datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S'),
                    'cmdline': process.cmdline(),
                    'connections': len(process.connections()),
                    'io_counters': process.io_counters()._asdict() if hasattr(process, 'io_counters') else None
                }
                
                self.process_cache[pid] = details
                return details
        
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            return {
                'pid': pid,
                'error': str(e),
                'memory_percent': 0,
                'cpu_percent': 0
            }
        except Exception as e:
            return {
                'pid': pid,
                'error': f'Unexpected error: {str(e)}',
                'memory_percent': 0,
                'cpu_percent': 0
            }
    
    def clear_cache(self):
        """Clear cache"""
        self.process_cache.clear()
    
    def get_network_connections(self):
        """Get all network connections"""
        connections = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                try:
                    if conn.pid:
                        process_details = self.get_process_details(conn.pid)
                        local_addr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "*:*"
                        remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "*:*"
                        
                        # Determine protocol type
                        if conn.type == socket.SOCK_STREAM:
                            protocol = 'TCP'
                        elif conn.type == socket.SOCK_DGRAM:
                            protocol = 'UDP'
                        else:
                            protocol = 'UNKNOWN'
                        
                        # Extend protocol information based on port number
                        if conn.laddr:
                            port = conn.laddr.port
                            if port in [80, 443]:
                                protocol += '/HTTP'
                            elif port == 53:
                                protocol += '/DNS'
                            elif port in [20, 21]:
                                protocol += '/FTP'
                            elif port == 22:
                                protocol += '/SSH'
                            elif port == 25:
                                protocol += '/SMTP'
                        
                        connection = {
                            'pid': conn.pid,
                            'process_name': self.get_process_name(conn.pid),
                            'protocol': protocol,
                            'local_address': local_addr,
                            'remote_address': remote_addr,
                            'status': conn.status,
                            'local_port': conn.laddr.port if conn.laddr else None,
                            'process_details': process_details
                        }
                        connections.append(connection)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"Error getting network connections: {str(e)}")
        
        return connections
    
    def get_grouped_processes(self):
        """Group processes by PID"""
        grouped_processes = {}
        
        try:
            for conn in psutil.net_connections(kind='inet'):
                try:
                    if conn.pid:
                        if conn.pid not in grouped_processes:
                            process_details = self.get_process_details(conn.pid)
                            grouped_processes[conn.pid] = {
                                'pid': conn.pid,
                                'process_name': self.get_process_name(conn.pid),
                                'connections': [],
                                'memory_percent': process_details.get('memory_percent', 0),
                                'cpu_percent': process_details.get('cpu_percent', 0),
                                'username': process_details.get('username', ''),
                                'create_time': process_details.get('create_time', ''),
                            }
                        
                        local_addr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "*:*"
                        remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "*:*"
                        
                        protocol = 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP'
                        if conn.laddr and conn.laddr.port:
                            port = conn.laddr.port
                            if port in [80, 443]: protocol += '/HTTP'
                            elif port == 53: protocol += '/DNS'
                            elif port in [20, 21]: protocol += '/FTP'
                            elif port == 22: protocol += '/SSH'
                            elif port == 25: protocol += '/SMTP'
                        
                        grouped_processes[conn.pid]['connections'].append({
                            'protocol': protocol,
                            'local_address': local_addr,
                            'remote_address': remote_addr,
                            'status': conn.status,
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"Error getting grouped processes: {str(e)}")
        
        return list(grouped_processes.values())
    
    def get_network_interfaces(self):
        """Get network interfaces"""
        interfaces = []
        
        try:
            # Get network interface statistics
            net_if_stats = psutil.net_if_stats()
            net_if_addrs = psutil.net_if_addrs()
            net_io_counters = psutil.net_io_counters(pernic=True)
            
            for interface_name, stats in net_if_stats.items():
                if not stats.isup:
                    continue  # Only show active interfaces
                    
                # Get IP addresses
                ip_addresses = []
                if interface_name in net_if_addrs:
                    for addr in net_if_addrs[interface_name]:
                        if addr.family == socket.AF_INET:  # IPv4
                            ip_addresses.append(addr.address)
                
                # Get I/O counters
                io_counters = net_io_counters.get(interface_name)
                
                interface_info = {
                    'name': interface_name,
                    'is_up': stats.isup,
                    'speed': stats.speed,  # Mbps
                    'mtu': stats.mtu,
                    'ip_addresses': ip_addresses,
                    'bytes_sent': io_counters.bytes_sent if io_counters else 0,
                    'bytes_recv': io_counters.bytes_recv if io_counters else 0,
                    'packets_sent': io_counters.packets_sent if io_counters else 0,
                    'packets_recv': io_counters.packets_recv if io_counters else 0,
                }
                
                interfaces.append(interface_info)
        
        except Exception as e:
            logger.error(f"Error getting network interfaces: {str(e)}")
        
        return interfaces
    
    def get_processes_by_interface(self):
        """Group processes by network interface"""
        interface_processes = defaultdict(lambda: {
            'connections': [],
            'processes': set(),
            'total_connections': 0
        })
        
        # Cache for process info (PID -> details)
        pid_cache = {}
        
        try:
            # First get all network interfaces
            net_if_addrs = psutil.net_if_addrs()
            interface_ips = {}
            
            # Collect IP addresses of each interface into a dict
            for interface_name, addrs in net_if_addrs.items():
                interface_ips[interface_name] = []
                for addr in addrs:
                    if addr.family == socket.AF_INET:  # IPv4
                        interface_ips[interface_name].append(addr.address)
            
            # Get all connections and group by interface
            for conn in psutil.net_connections(kind='inet'):
                try:
                    if not conn.pid or not conn.laddr:
                        continue
                    
                    local_ip = conn.laddr.ip
                    matched_interface = None
                    
                    # Find which interface it belongs to
                    for interface_name, ips in interface_ips.items():
                        if local_ip in ips:
                            matched_interface = interface_name
                            break
                    
                    # If no match, perform general IP check
                    if not matched_interface:
                        if local_ip == '0.0.0.0' or local_ip == '127.0.0.1':
                            matched_interface = 'Loopback/All'
                        else:
                            matched_interface = 'Unknown'
                    
                    # Get process info from cache or fetch once per PID
                    if conn.pid not in pid_cache:
                        process_name = self.get_process_name(conn.pid)
                        # Use cached process details if available
                        if conn.pid in self.process_cache:
                            process_details = self.process_cache[conn.pid]
                        else:
                            # Get minimal info without expensive CPU calculation
                            try:
                                proc = psutil.Process(conn.pid)
                                process_details = {
                                    'memory_percent': proc.memory_percent(),
                                    'cpu_percent': 0  # Skip expensive CPU calculation
                                }
                            except:
                                process_details = {'memory_percent': 0, 'cpu_percent': 0}
                        
                        pid_cache[conn.pid] = {
                            'name': process_name,
                            'details': process_details
                        }
                    
                    cached_info = pid_cache[conn.pid]
                    
                    local_addr = f"{conn.laddr.ip}:{conn.laddr.port}"
                    remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "*:*"
                    
                    protocol = 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP'
                    if conn.laddr.port:
                        port = conn.laddr.port
                        if port in [80, 443]: protocol += '/HTTP'
                        elif port == 53: protocol += '/DNS'
                        elif port in [20, 21]: protocol += '/FTP'
                        elif port == 22: protocol += '/SSH'
                        elif port == 25: protocol += '/SMTP'
                    
                    interface_processes[matched_interface]['connections'].append({
                        'pid': conn.pid,
                        'process_name': cached_info['name'],
                        'protocol': protocol,
                        'local_address': local_addr,
                        'remote_address': remote_addr,
                        'status': conn.status,
                        'memory_percent': cached_info['details'].get('memory_percent', 0),
                        'cpu_percent': cached_info['details'].get('cpu_percent', 0),
                    })
                    
                    interface_processes[matched_interface]['processes'].add(cached_info['name'])
                    interface_processes[matched_interface]['total_connections'] += 1
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        
        except Exception as e:
            logger.error(f"Error getting processes by interface: {str(e)}")
        
        # Format result
        result = []
        for interface_name, data in interface_processes.items():
            result.append({
                'interface_name': interface_name,
                'total_connections': data['total_connections'],
                'unique_processes': len(data['processes']),
                'connections': data['connections']
            })
        
        # Sort by connection count
        result.sort(key=lambda x: x['total_connections'], reverse=True)
        
        return result
    
    def get_most_used_ports(self, limit=None):
        """Get most used ports"""
        port_connections = defaultdict(lambda: {
            'connections': [],
            'count': 0,
            'processes': set()
        })
        
        try:
            for conn in psutil.net_connections(kind='inet'):
                try:
                    if not conn.laddr:
                        continue
                    
                    port = conn.laddr.port
                    
                    # Collect port information
                    port_connections[port]['count'] += 1
                    
                    if conn.pid:
                        process_name = self.get_process_name(conn.pid)
                        port_connections[port]['processes'].add(process_name if process_name else 'Unknown')
                        
                        local_addr = f"{conn.laddr.ip}:{conn.laddr.port}"
                        remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "-"
                        
                        port_connections[port]['connections'].append({
                            'pid': conn.pid,
                            'process_name': process_name,
                            'local_address': local_addr,
                            'remote_address': remote_addr,
                            'status': conn.status,
                        })
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        
        except Exception as e:
            logger.error(f"Error getting ports: {str(e)}")
        
        # Format results
        result = []
        for port, data in port_connections.items():
            # Determine service name for port
            service_name = self._get_service_name(port)
            
            result.append({
                'port': port,
                'connection_count': data['count'],
                'service_name': service_name,
                'processes': list(data['processes']),
                'status': 'Unknown' if data['count'] == 0 else 'Unknown'
            })
        
        # Sort by connection count
        result.sort(key=lambda x: x['connection_count'], reverse=True)
        
        # Apply limit if exists
        if limit:
            result = result[:limit]
        
        return result
    
    def get_port_details(self, port):
        """Get detailed information for a specific port"""
        try:
            port = int(port)
            connections = []
            process_stats = {}
            
            for conn in psutil.net_connections(kind='inet'):
                try:
                    if not conn.laddr or conn.laddr.port != port:
                        continue
                    
                    local_addr = f"{conn.laddr.ip}:{conn.laddr.port}"
                    remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "-"
                    
                    connection_data = {
                        'local_address': local_addr,
                        'remote_address': remote_addr,
                        'status': conn.status,
                        'pid': conn.pid if conn.pid else '-'
                    }
                    
                    connections.append(connection_data)
                    
                    # Collect process statistics
                    if conn.pid and conn.pid not in process_stats:
                        try:
                            process = psutil.Process(conn.pid)
                            memory_info = process.memory_info()
                            
                            # I/O counters
                            io_read = 0
                            io_write = 0
                            try:
                                io_counters = process.io_counters()
                                io_read = io_counters.read_bytes
                                io_write = io_counters.write_bytes
                            except (psutil.AccessDenied, AttributeError):
                                pass
                            
                            process_stats[conn.pid] = {
                                'process_name': process.name(),
                                'pid': conn.pid,
                                'cpu_percent': process.cpu_percent(interval=0.1),
                                'memory_mb': memory_info.rss / (1024 * 1024),
                                'io_read': io_read,
                                'io_read_formatted': self._format_bytes(io_read),
                                'io_write': io_write,
                                'io_write_formatted': self._format_bytes(io_write)
                            }
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Service name for port
            service_name = self._get_service_name(port)
            
            return {
                'port': port,
                'service_name': service_name,
                'total_connections': len(connections),
                'connections': connections,
                'processes': list(process_stats.values())
            }
        
        except Exception as e:
            logger.error(f"Error getting port details: {str(e)}")
            return None
    
    def _get_service_name(self, port):
        """Determine service name from port number"""
        common_ports = {
            20: 'FTP Data',
            21: 'FTP',
            22: 'SSH',
            23: 'Telnet',
            25: 'SMTP',
            53: 'DNS',
            80: 'HTTP',
            110: 'POP3',
            143: 'IMAP',
            443: 'HTTPS',
            445: 'SMB',
            3306: 'MySQL',
            3389: 'RDP',
            5432: 'PostgreSQL',
            5900: 'VNC',
            6379: 'Redis',
            8000: 'HTTP Alt',
            8080: 'HTTP Proxy',
            8443: 'HTTPS Alt',
            27017: 'MongoDB'
        }
        
        return common_ports.get(port, 'Unknown')
    
    def get_detailed_process_info(self, pid):
        """Get very detailed process information"""
        try:
            process = psutil.Process(pid)
            
            # Try to get basic information first
            info = {
                'pid': pid,
                'name': 'Unknown',
                'status': 'Unknown',
                'username': 'N/A',
                'create_time': 'N/A',
                'cpu_percent': 0.0,
                'memory_percent': 0.0,
                'num_threads': 0,
                'nice': 0,
                'ppid': 0,
                'access_denied': False,
                'partial_data': False
            }
            
            # Try to get each piece of information separately
            # This allows us to get partial data even if some operations fail
            
            try:
                info['name'] = process.name()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                info['access_denied'] = True
                info['partial_data'] = True
            
            try:
                info['status'] = process.status()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            try:
                info['username'] = process.username()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                info['username'] = 'Access Denied'
            
            try:
                info['create_time'] = datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S')
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            try:
                info['cpu_percent'] = process.cpu_percent(interval=0.1)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            try:
                info['memory_percent'] = process.memory_percent()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            try:
                info['num_threads'] = process.num_threads()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            try:
                info['nice'] = process.nice()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            try:
                info['ppid'] = process.ppid()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            # Memory information
            try:
                memory_info = process.memory_info()
                info['memory_info'] = {
                    'rss': memory_info.rss,
                    'rss_formatted': self._format_bytes(memory_info.rss),
                    'vms': memory_info.vms,
                    'vms_formatted': self._format_bytes(memory_info.vms)
                }
            except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                info['memory_info'] = {
                    'rss': 0,
                    'rss_formatted': '0 B',
                    'vms': 0,
                    'vms_formatted': '0 B'
                }
                info['partial_data'] = True
            
            # I/O information
            try:
                io_counters = process.io_counters()
                info['io_counters'] = {
                    'read_bytes': io_counters.read_bytes,
                    'read_formatted': self._format_bytes(io_counters.read_bytes),
                    'write_bytes': io_counters.write_bytes,
                    'write_formatted': self._format_bytes(io_counters.write_bytes)
                }
            except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                info['io_counters'] = None
                info['partial_data'] = True
            
            # Connections
            try:
                connections = process.connections()
                info['connections'] = []
                for conn in connections:  # All connections
                    laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None
                    raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None
                    info['connections'].append({
                        'laddr': laddr,
                        'raddr': raddr,
                        'status': conn.status
                    })
            except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                info['connections'] = []
                info['partial_data'] = True
            
            # Child processes
            try:
                children = process.children()
                info['children'] = [{'pid': child.pid, 'name': child.name()} for child in children]
            except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                info['children'] = []
                info['partial_data'] = True
            
            # Available actions
            try:
                info['available_actions'] = self._get_available_actions(info['status'])
            except:
                info['available_actions'] = []
            
            # Add warning message if access was denied
            if info['access_denied'] or info['partial_data']:
                info['warning'] = 'Limited access to this process. Some information may be unavailable due to system restrictions.'
            
            return info
        
        except psutil.NoSuchProcess as e:
            logger.error(f"Process {pid} does not exist: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting info for PID {pid}: {str(e)}")
            # Return minimal info even on unexpected errors
            return {
                'pid': pid,
                'name': 'Unknown',
                'status': 'Unknown',
                'error': str(e),
                'access_denied': True,
                'warning': f'Unable to retrieve process information: {str(e)}'
            }
    
    def _format_bytes(self, bytes_value):
        """Convert byte value to readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    def _get_available_actions(self, status):
        """Determine available actions based on process status"""
        actions = []
        
        if status in ['running', 'sleeping']:
            actions.extend(['stop', 'kill', 'suspend'])
        
        if status == 'stopped':
            actions.append('resume')
        
        if status in ['running', 'sleeping', 'stopped']:
            actions.append('restart')
        
        return actions
    
    def search_connections(self, search_type, search_value):
        """
        Search connections by PID, Port, or IP
        Returns detailed information about all matching connections
        """
        results = {
            'search_type': search_type,
            'search_value': search_value,
            'total_connections': 0,
            'unique_processes': set(),
            'unique_ports': set(),
            'unique_ips': set(),
            'connections': [],
            'process_details': {},
            'port_details': {},
            'summary': {}
        }
        
        try:
            all_connections = psutil.net_connections(kind='inet')
            
            for conn in all_connections:
                match = False
                
                # Check if connection matches search criteria
                if search_type == 'pid':
                    if conn.pid and str(conn.pid) == str(search_value):
                        match = True
                
                elif search_type == 'port':
                    try:
                        port_value = int(search_value)
                        if conn.laddr and conn.laddr.port == port_value:
                            match = True
                        elif conn.raddr and conn.raddr.port == port_value:
                            match = True
                    except ValueError:
                        continue
                
                elif search_type == 'ip':
                    if conn.laddr and conn.laddr.ip == search_value:
                        match = True
                    elif conn.raddr and conn.raddr.ip == search_value:
                        match = True
                
                if match:
                    # Get process details
                    process_name = self.get_process_name(conn.pid) if conn.pid else "Unknown"
                    
                    if conn.pid and conn.pid not in results['process_details']:
                        process_details = self.get_process_details(conn.pid)
                        if process_details:
                            results['process_details'][conn.pid] = process_details
                    
                    # Format addresses
                    local_addr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "*:*"
                    remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "*:*"
                    
                    # Get protocol
                    protocol = 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP'
                    if conn.laddr and conn.laddr.port:
                        port = conn.laddr.port
                        if port in [80, 443]: protocol += '/HTTP'
                        elif port == 53: protocol += '/DNS'
                        elif port in [20, 21]: protocol += '/FTP'
                        elif port == 22: protocol += '/SSH'
                        elif port == 25: protocol += '/SMTP'
                    
                    # Add connection
                    conn_data = {
                        'pid': conn.pid,
                        'process_name': process_name,
                        'protocol': protocol,
                        'local_address': local_addr,
                        'remote_address': remote_addr,
                        'status': conn.status,
                        'local_ip': conn.laddr.ip if conn.laddr else None,
                        'local_port': conn.laddr.port if conn.laddr else None,
                        'remote_ip': conn.raddr.ip if conn.raddr else None,
                        'remote_port': conn.raddr.port if conn.raddr else None
                    }
                    
                    results['connections'].append(conn_data)
                    results['total_connections'] += 1
                    
                    # Track unique values
                    if conn.pid:
                        results['unique_processes'].add(process_name)
                    if conn.laddr:
                        results['unique_ports'].add(conn.laddr.port)
                        results['unique_ips'].add(conn.laddr.ip)
                    if conn.raddr:
                        results['unique_ports'].add(conn.raddr.port)
                        results['unique_ips'].add(conn.raddr.ip)
                    
                    # Track port usage
                    if conn.laddr and conn.laddr.port:
                        port = conn.laddr.port
                        if port not in results['port_details']:
                            results['port_details'][port] = {
                                'port': port,
                                'service_name': self._get_service_name(port),
                                'connection_count': 0,
                                'processes': set()
                            }
                        results['port_details'][port]['connection_count'] += 1
                        if conn.pid:
                            results['port_details'][port]['processes'].add(process_name)
            
            # Format results
            results['unique_processes'] = list(results['unique_processes'])
            results['unique_ports'] = sorted(list(results['unique_ports']))
            results['unique_ips'] = list(results['unique_ips'])
            
            # Format port details
            port_details_list = []
            for port_data in results['port_details'].values():
                port_data['processes'] = list(port_data['processes'])
                port_details_list.append(port_data)
            results['port_details'] = sorted(port_details_list, key=lambda x: x['connection_count'], reverse=True)
            
            # Create summary
            results['summary'] = {
                'total_connections': results['total_connections'],
                'unique_processes': len(results['unique_processes']),
                'unique_ports': len(results['unique_ports']),
                'unique_ips': len(results['unique_ips']),
                'search_performed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"Search completed: {search_type}={search_value}, found {results['total_connections']} connections")
            
        except Exception as e:
            logger.error(f"Error searching connections: {str(e)}")
            results['error'] = str(e)
        
        return results


class ProcessManager:
    """Class for process management operations"""
    
    @staticmethod
    def terminate_process(pid):
        """Terminate process"""
        try:
            process = psutil.Process(pid)
            process.terminate()
            return {'success': True, 'message': f'Process {pid} terminated successfully'}
        except psutil.NoSuchProcess:
            return {'success': False, 'error': 'Process not found'}
        except psutil.AccessDenied:
            return {'success': False, 'error': 'Access denied'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def kill_process(pid):
        """Force kill process"""
        try:
            process = psutil.Process(pid)
            process.kill()
            return {'success': True, 'message': f'Process {pid} killed forcefully'}
        except psutil.NoSuchProcess:
            return {'success': False, 'error': 'Process not found'}
        except psutil.AccessDenied:
            return {'success': False, 'error': 'Access denied'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def suspend_process(pid):
        """Suspend process"""
        try:
            process = psutil.Process(pid)
            process.suspend()
            return {'success': True, 'message': f'Process {pid} suspended'}
        except psutil.NoSuchProcess:
            return {'success': False, 'error': 'Process not found'}
        except psutil.AccessDenied:
            return {'success': False, 'error': 'Access denied'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def resume_process(pid):
        """Resume process"""
        try:
            process = psutil.Process(pid)
            process.resume()
            return {'success': True, 'message': f'Process {pid} resumed'}
        except psutil.NoSuchProcess:
            return {'success': False, 'error': 'Process not found'}
        except psutil.AccessDenied:
            return {'success': False, 'error': 'Access denied'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Global instances
process_monitor = ProcessMonitor()
process_manager = ProcessManager()

