"""
IP Analysis Module
Detaylı IP analizi ve request tracking için
"""

import psutil
import socket
import requests
import json
import time
from datetime import datetime, timezone
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional
import logging
from django.http import JsonResponse
from django.utils import timezone as django_timezone

logger = logging.getLogger(__name__)


class IPAnalyzer:
    """IP analizi ve request tracking sınıfı"""
    
    def __init__(self):
        self.request_history = defaultdict(list)
        self.connection_cache = {}
        self.last_update = None
    
    def get_ip_analysis(self) -> List[Dict[str, Any]]:
        """Tüm IP adreslerinin analizini döndür"""
        try:
            # Network connections'ları al
            connections = psutil.net_connections(kind='inet')
            ip_data = defaultdict(lambda: {
                'connections': [],
                'processes': set(),
                'ports': set(),
                'request_count': 0,
                'last_activity': None
            })
            
            # Her connection'ı analiz et
            for conn in connections:
                if not conn.laddr or not conn.raddr:
                    continue
                
                # Local ve remote IP'leri al
                local_ip = conn.laddr.ip
                remote_ip = conn.raddr.ip
                
                # Process bilgilerini al
                process_name = 'Unknown'
                pid = None
                if conn.pid:
                    try:
                        process = psutil.Process(conn.pid)
                        process_name = process.name()
                        pid = conn.pid
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Connection bilgilerini kaydet
                conn_info = {
                    'local_address': f"{local_ip}:{conn.laddr.port}",
                    'remote_address': f"{remote_ip}:{conn.raddr.port}",
                    'status': conn.status,
                    'process_name': process_name,
                    'pid': pid,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
                # Her IP için veri topla
                for ip in [local_ip, remote_ip]:
                    if ip and ip != '127.0.0.1':  # Localhost'u hariç tut
                        ip_data[ip]['connections'].append(conn_info)
                        ip_data[ip]['processes'].add(process_name)
                        ip_data[ip]['ports'].add(conn.laddr.port if ip == local_ip else conn.raddr.port)
                        ip_data[ip]['last_activity'] = datetime.now(timezone.utc).isoformat()
            
            # IP analiz sonuçlarını formatla
            results = []
            for ip, data in ip_data.items():
                # IP tipini belirle
                ip_type = self._get_ip_type(ip)
                
                # Status belirle
                status = 'active' if len(data['connections']) > 0 else 'inactive'
                
                # Request history'den request sayısını al
                request_count = len(self.request_history.get(ip, []))
                
                results.append({
                    'ip': ip,
                    'ip_type': ip_type,
                    'status': status,
                    'connection_count': len(data['connections']),
                    'process_count': len(data['processes']),
                    'port_count': len(data['ports']),
                    'request_count': request_count,
                    'last_activity': data['last_activity'],
                    'location': self._get_ip_location(ip),
                    'processes': list(data['processes']),
                    'ports': list(data['ports'])
                })
            
            # Connection count'a göre sırala
            results.sort(key=lambda x: x['connection_count'], reverse=True)
            
            self.last_update = datetime.now(timezone.utc).isoformat()
            return results
            
        except Exception as e:
            logger.error(f"IP Analysis error: {str(e)}")
            return []
    
    def get_ip_details(self, ip: str) -> Dict[str, Any]:
        """Belirli bir IP için detaylı analiz döndür"""
        try:
            # IP bilgilerini al
            ip_type = self._get_ip_type(ip)
            location = self._get_ip_location(ip)
            
            # Network connections'ları al
            connections = psutil.net_connections(kind='inet')
            ip_connections = []
            processes = set()
            ports = set()
            
            for conn in connections:
                if not conn.laddr or not conn.raddr:
                    continue
                
                # Bu IP ile ilgili connection'ları bul
                if (conn.laddr.ip == ip or conn.raddr.ip == ip):
                    process_name = 'Unknown'
                    pid = None
                    if conn.pid:
                        try:
                            process = psutil.Process(conn.pid)
                            process_name = process.name()
                            pid = conn.pid
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    
                    ip_connections.append({
                        'local_address': f"{conn.laddr.ip}:{conn.laddr.port}",
                        'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}",
                        'status': conn.status,
                        'process_name': process_name,
                        'pid': pid
                    })
                    
                    processes.add(process_name)
                    ports.add(conn.laddr.port if conn.laddr.ip == ip else conn.raddr.port)
            
            # Detaylı request history'yi al
            detailed_requests = self._get_detailed_request_history(ip)
            
            # Request istatistiklerini hesapla
            request_stats = self._calculate_request_statistics(detailed_requests)
            
            # Target server analizi
            target_servers = set()
            for conn in ip_connections:
                if conn.get('remote_address'):
                    target_servers.add(conn['remote_address'])
            
            server_analysis = self._analyze_target_servers(target_servers)
            
            # Son aktivite zamanını belirle
            last_activity = None
            if detailed_requests:
                last_activity = max(req.get('timestamp', '') for req in detailed_requests)
            
            return {
                'ip_type': ip_type,
                'location': location,
                'status': 'active' if ip_connections else 'inactive',
                'total_connections': len(ip_connections),
                'process_count': len(processes),
                'port_count': len(ports),
                'last_activity': last_activity,
                'connections': ip_connections,
                'requests': detailed_requests,
                'processes': list(processes),
                'ports': list(ports),
                'target_servers': list(target_servers),
                'request_statistics': request_stats,
                'server_analysis': server_analysis,
                'detailed_analysis': self._get_detailed_analysis(ip, detailed_requests, ip_connections)
            }
            
        except Exception as e:
            logger.error(f"IP Details error: {str(e)}")
            return {
                'ip_type': 'Unknown',
                'location': 'Unknown',
                'status': 'error',
                'total_connections': 0,
                'process_count': 0,
                'port_count': 0,
                'last_activity': None,
                'connections': [],
                'requests': [],
                'processes': [],
                'ports': []
            }
    
    def _get_ip_type(self, ip: str) -> str:
        """IP tipini belirle"""
        try:
            # Private IP aralıkları
            if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
                return 'Private'
            elif ip == '127.0.0.1':
                return 'Localhost'
            elif ip.startswith('169.254.'):
                return 'Link-Local'
            else:
                return 'Public'
        except:
            return 'Unknown'
    
    def _get_ip_location(self, ip: str) -> str:
        """IP lokasyonunu belirle (basit implementasyon)"""
        try:
            # Private IP'ler için
            if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
                return 'Local Network'
            elif ip == '127.0.0.1':
                return 'Localhost'
            else:
                # Public IP'ler için (gerçek implementasyonda IP geolocation API kullanılabilir)
                return 'External'
        except:
            return 'Unknown'
    
    def log_request(self, ip: str, method: str, path: str, status: int, 
                   response_time: int, user_agent: str = None):
        """IP için request log'u kaydet"""
        try:
            request_data = {
                'method': method.upper(),
                'path': path,
                'status': status,
                'status_class': 'success' if 200 <= status < 300 else 'error' if status >= 400 else 'warning',
                'response_time': response_time,
                'user_agent': user_agent,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self.request_history[ip].append(request_data)
            
            # Son 100 request'i tut (memory management)
            if len(self.request_history[ip]) > 100:
                self.request_history[ip] = self.request_history[ip][-100:]
                
        except Exception as e:
            logger.error(f"Request logging error: {str(e)}")
    
    def get_request_statistics(self, ip: str) -> Dict[str, Any]:
        """IP için request istatistiklerini döndür"""
        try:
            requests = self.request_history.get(ip, [])
            if not requests:
                return {
                    'total_requests': 0,
                    'success_rate': 0,
                    'avg_response_time': 0,
                    'most_common_paths': [],
                    'method_distribution': {}
                }
            
            # İstatistikleri hesapla
            total_requests = len(requests)
            successful_requests = len([r for r in requests if 200 <= r['status'] < 300])
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            
            response_times = [r['response_time'] for r in requests if r['response_time']]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # En çok kullanılan path'ler
            path_counter = Counter([r['path'] for r in requests])
            most_common_paths = path_counter.most_common(5)
            
            # Method dağılımı
            method_counter = Counter([r['method'] for r in requests])
            method_distribution = dict(method_counter)
            
            return {
                'total_requests': total_requests,
                'success_rate': round(success_rate, 2),
                'avg_response_time': round(avg_response_time, 2),
                'most_common_paths': most_common_paths,
                'method_distribution': method_distribution
            }
            
        except Exception as e:
            logger.error(f"Request statistics error: {str(e)}")
            return {
                'total_requests': 0,
                'success_rate': 0,
                'avg_response_time': 0,
                'most_common_paths': [],
                'method_distribution': {}
            }
    
    def clear_request_history(self, ip: str = None):
        """Request history'yi temizle"""
        try:
            if ip:
                if ip in self.request_history:
                    del self.request_history[ip]
            else:
                self.request_history.clear()
                
        except Exception as e:
            logger.error(f"Clear request history error: {str(e)}")
    
    def _get_detailed_request_history(self, ip: str) -> List[Dict[str, Any]]:
        """IP için detaylı request history döndür - sadece gerçek veriler"""
        try:
            # Sadece gerçek request history'yi döndür
            return self.request_history.get(ip, [])
            
        except Exception as e:
            logger.error(f"Detailed request history error: {str(e)}")
            return []
    
    def _calculate_request_statistics(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Request istatistiklerini hesapla"""
        try:
            if not requests:
                return {
                    'total_requests': 0,
                    'method_distribution': {},
                    'status_code_distribution': {},
                    'avg_response_time': 0,
                    'total_data_transferred': 0,
                    'most_common_paths': [],
                    'peak_hours': [],
                    'error_rate': 0
                }
            
            # Method dağılımı
            methods = [req.get('method', 'UNKNOWN') for req in requests]
            method_dist = dict(Counter(methods))
            
            # Status code dağılımı
            status_codes = [req.get('status_code', 0) for req in requests]
            status_dist = dict(Counter(status_codes))
            
            # Ortalama response time
            response_times = [req.get('response_time', 0) for req in requests if req.get('response_time')]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Toplam data transfer
            total_data = sum(req.get('request_size', 0) + req.get('response_size', 0) for req in requests)
            
            # En çok kullanılan path'ler
            paths = [req.get('path', '') for req in requests]
            path_dist = dict(Counter(paths))
            most_common_paths = sorted(path_dist.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Error rate
            error_requests = [req for req in requests if req.get('status_code', 0) >= 400]
            error_rate = (len(error_requests) / len(requests)) * 100 if requests else 0
            
            return {
                'total_requests': len(requests),
                'method_distribution': method_dist,
                'status_code_distribution': status_dist,
                'avg_response_time': round(avg_response_time, 2),
                'total_data_transferred': total_data,
                'most_common_paths': most_common_paths,
                'peak_hours': self._get_peak_hours(requests),
                'error_rate': round(error_rate, 2)
            }
            
        except Exception as e:
            logger.error(f"Request statistics error: {str(e)}")
            return {}
    
    def _analyze_target_servers(self, target_servers: set) -> Dict[str, Any]:
        """Target server'ları analiz et"""
        try:
            if not target_servers:
                return {}
            
            server_analysis = {}
            for server in target_servers:
                ip, port = server.split(':')
                port = int(port)
                
                # Port tipini belirle
                port_type = self._get_port_type(port)
                
                # Server tipini belirle
                server_type = self._get_server_type(ip, port)
                
                server_analysis[server] = {
                    'ip': ip,
                    'port': port,
                    'port_type': port_type,
                    'server_type': server_type,
                    'is_secure': port in [443, 8443, 9443],
                    'is_common_service': port in [80, 443, 22, 21, 25, 53, 110, 143, 993, 995]
                }
            
            return server_analysis
            
        except Exception as e:
            logger.error(f"Server analysis error: {str(e)}")
            return {}
    
    def _get_detailed_analysis(self, ip: str, requests: List[Dict[str, Any]], connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """IP için detaylı analiz döndür"""
        try:
            # Security analysis
            security_analysis = self._analyze_security_patterns(ip, requests, connections)
            
            # Behavioral analysis
            behavioral_analysis = self._analyze_behavior_patterns(ip, requests, connections)
            
            # Performance analysis
            performance_analysis = self._analyze_performance_patterns(ip, requests, connections)
            
            return {
                'security_analysis': security_analysis,
                'behavioral_analysis': behavioral_analysis,
                'performance_analysis': performance_analysis,
                'risk_score': self._calculate_risk_score(ip, requests, connections),
                'recommendations': self._get_recommendations(ip, requests, connections)
            }
            
        except Exception as e:
            logger.error(f"Detailed analysis error: {str(e)}")
            return {}
    
    def _get_port_type(self, port: int) -> str:
        """Port tipini belirle"""
        common_ports = {
            80: 'HTTP', 443: 'HTTPS', 22: 'SSH', 21: 'FTP', 25: 'SMTP',
            53: 'DNS', 110: 'POP3', 143: 'IMAP', 993: 'IMAPS', 995: 'POP3S',
            3389: 'RDP', 5900: 'VNC', 5432: 'PostgreSQL', 3306: 'MySQL',
            6379: 'Redis', 27017: 'MongoDB', 9200: 'Elasticsearch'
        }
        return common_ports.get(port, 'Custom')
    
    def _get_server_type(self, ip: str, port: int) -> str:
        """Server tipini belirle"""
        if port in [80, 443]:
            return 'Web Server'
        elif port in [22, 3389, 5900]:
            return 'Remote Access'
        elif port in [25, 110, 143, 993, 995]:
            return 'Mail Server'
        elif port in [5432, 3306, 6379, 27017, 9200]:
            return 'Database Server'
        else:
            return 'Unknown Service'
    
    def _get_peak_hours(self, requests: List[Dict[str, Any]]) -> List[str]:
        """Peak saatleri belirle"""
        try:
            hours = []
            for req in requests:
                timestamp = req.get('timestamp', '')
                if timestamp:
                    hour = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).hour
                    hours.append(hour)
            
            if hours:
                hour_dist = dict(Counter(hours))
                peak_hours = sorted(hour_dist.items(), key=lambda x: x[1], reverse=True)[:3]
                return [f"{hour}:00 ({count} requests)" for hour, count in peak_hours]
            
            return []
            
        except Exception as e:
            logger.error(f"Peak hours error: {str(e)}")
            return []
    
    def _analyze_security_patterns(self, ip: str, requests: List[Dict[str, Any]], connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Güvenlik pattern'lerini analiz et"""
        try:
            # Suspicious patterns
            suspicious_requests = [req for req in requests if req.get('status_code', 0) >= 400]
            failed_auth_attempts = [req for req in requests if req.get('path', '').find('login') != -1 and req.get('status_code', 0) == 401]
            
            # Port scanning detection
            unique_ports = set(conn.get('remote_address', '').split(':')[-1] for conn in connections)
            port_scanning = len(unique_ports) > 10
            
            return {
                'suspicious_requests': len(suspicious_requests),
                'failed_auth_attempts': len(failed_auth_attempts),
                'port_scanning_detected': port_scanning,
                'unique_ports_accessed': len(unique_ports),
                'security_risk_level': 'High' if len(failed_auth_attempts) > 5 or port_scanning else 'Medium' if len(suspicious_requests) > 3 else 'Low'
            }
            
        except Exception as e:
            logger.error(f"Security analysis error: {str(e)}")
            return {}
    
    def _analyze_behavior_patterns(self, ip: str, requests: List[Dict[str, Any]], connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Davranış pattern'lerini analiz et"""
        try:
            # Request frequency
            request_frequency = len(requests) / 24 if requests else 0  # requests per hour
            
            # Method diversity
            methods = [req.get('method', '') for req in requests]
            method_diversity = len(set(methods))
            
            # Path diversity
            paths = [req.get('path', '') for req in requests]
            path_diversity = len(set(paths))
            
            # Time patterns
            time_patterns = self._analyze_time_patterns(requests)
            
            return {
                'request_frequency': round(request_frequency, 2),
                'method_diversity': method_diversity,
                'path_diversity': path_diversity,
                'time_patterns': time_patterns,
                'behavior_type': 'Aggressive' if request_frequency > 10 else 'Normal' if request_frequency > 1 else 'Passive'
            }
            
        except Exception as e:
            logger.error(f"Behavior analysis error: {str(e)}")
            return {}
    
    def _analyze_performance_patterns(self, ip: str, requests: List[Dict[str, Any]], connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Performance pattern'lerini analiz et"""
        try:
            response_times = [req.get('response_time', 0) for req in requests if req.get('response_time')]
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)
                
                # Performance rating
                if avg_response_time < 100:
                    performance_rating = 'Excellent'
                elif avg_response_time < 500:
                    performance_rating = 'Good'
                elif avg_response_time < 1000:
                    performance_rating = 'Average'
                else:
                    performance_rating = 'Poor'
            else:
                avg_response_time = 0
                max_response_time = 0
                min_response_time = 0
                performance_rating = 'Unknown'
            
            return {
                'avg_response_time': round(avg_response_time, 2),
                'max_response_time': max_response_time,
                'min_response_time': min_response_time,
                'performance_rating': performance_rating,
                'total_connections': len(connections),
                'active_connections': len([conn for conn in connections if conn.get('status') == 'ESTABLISHED'])
            }
            
        except Exception as e:
            logger.error(f"Performance analysis error: {str(e)}")
            return {}
    
    def _analyze_time_patterns(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Zaman pattern'lerini analiz et"""
        try:
            if not requests:
                return {}
            
            hours = []
            for req in requests:
                timestamp = req.get('timestamp', '')
                if timestamp:
                    hour = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).hour
                    hours.append(hour)
            
            if hours:
                hour_dist = dict(Counter(hours))
                most_active_hour = max(hour_dist.items(), key=lambda x: x[1])
                
                return {
                    'most_active_hour': f"{most_active_hour[0]}:00 ({most_active_hour[1]} requests)",
                    'activity_distribution': hour_dist,
                    'is_business_hours': any(9 <= h <= 17 for h in hours),
                    'is_night_activity': any(22 <= h or h <= 6 for h in hours)
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Time patterns error: {str(e)}")
            return {}
    
    def _calculate_risk_score(self, ip: str, requests: List[Dict[str, Any]], connections: List[Dict[str, Any]]) -> int:
        """Risk skoru hesapla (0-100)"""
        try:
            risk_score = 0
            
            # Failed requests
            failed_requests = len([req for req in requests if req.get('status_code', 0) >= 400])
            risk_score += min(failed_requests * 5, 30)
            
            # Port scanning
            unique_ports = set(conn.get('remote_address', '').split(':')[-1] for conn in connections)
            if len(unique_ports) > 10:
                risk_score += 25
            
            # High frequency requests
            if len(requests) > 50:
                risk_score += 20
            
            # Suspicious paths
            suspicious_paths = ['/admin', '/login', '/api/auth', '/.env', '/config']
            suspicious_count = sum(1 for req in requests if any(path in req.get('path', '') for path in suspicious_paths))
            risk_score += min(suspicious_count * 3, 15)
            
            # Error rate
            if requests:
                error_rate = (failed_requests / len(requests)) * 100
                if error_rate > 50:
                    risk_score += 10
            
            return min(risk_score, 100)
            
        except Exception as e:
            logger.error(f"Risk score calculation error: {str(e)}")
            return 0
    
    def _get_recommendations(self, ip: str, requests: List[Dict[str, Any]], connections: List[Dict[str, Any]]) -> List[str]:
        """Öneriler döndür"""
        try:
            recommendations = []
            
            # High error rate
            if requests:
                error_rate = (len([req for req in requests if req.get('status_code', 0) >= 400]) / len(requests)) * 100
                if error_rate > 30:
                    recommendations.append("High error rate detected. Check application logs and server health.")
            
            # Port scanning
            unique_ports = set(conn.get('remote_address', '').split(':')[-1] for conn in connections)
            if len(unique_ports) > 10:
                recommendations.append("Multiple port access detected. Consider implementing port restrictions.")
            
            # High frequency requests
            if len(requests) > 100:
                recommendations.append("High request frequency detected. Consider implementing rate limiting.")
            
            # Suspicious paths
            suspicious_paths = ['/admin', '/login', '/api/auth']
            suspicious_count = sum(1 for req in requests if any(path in req.get('path', '') for path in suspicious_paths))
            if suspicious_count > 5:
                recommendations.append("Multiple authentication attempts detected. Monitor for brute force attacks.")
            
            if not recommendations:
                recommendations.append("No significant issues detected. Normal activity pattern.")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Recommendations error: {str(e)}")
            return ["Unable to generate recommendations due to analysis error."]
    
    def get_ip_analysis_api(self, request):
        """IP analizi için API endpoint"""
        try:
            # IP analizi için veri topla
            ip_analysis = self.get_ip_analysis()
            
            return JsonResponse({
                'success': True,
                'ips': ip_analysis,
                'timestamp': django_timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"IP Analysis API error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def get_ip_details_api(self, request):
        """Belirli bir IP için detaylı analiz API endpoint"""
        try:
            ip = request.GET.get('ip')
            if not ip:
                return JsonResponse({
                    'success': False,
                    'error': 'IP parameter is required'
                }, status=400)
            
            # IP detaylarını al
            ip_details = self.get_ip_details(ip)
            
            # JavaScript'te beklenen format için dönüştür
            formatted_details = {
                'success': True,
                'ip': ip,
                'status': ip_details.get('status', 'inactive'),
                'connection_summary': {
                    'total_connections': ip_details.get('total_connections', 0),
                    'unique_processes': ip_details.get('process_count', 0),
                    'unique_ports': ip_details.get('port_count', 0)
                },
                'active_connections': [
                    {
                        'local_port': conn.get('local_address', '').split(':')[-1] if ':' in conn.get('local_address', '') else '0',
                        'remote_port': conn.get('remote_address', '').split(':')[-1] if ':' in conn.get('remote_address', '') else '0',
                        'status': conn.get('status', 'unknown'),
                        'process_name': conn.get('process_name', 'Unknown')
                    } for conn in ip_details.get('connections', [])
                ],
                'associated_processes': [
                    {
                        'name': process,
                        'pid': None,  # PID bilgisi connections'dan alınabilir
                        'cpu_percent': 0,
                        'memory_percent': 0
                    } for process in ip_details.get('processes', [])
                ],
                'request_statistics': ip_details.get('request_statistics', {}),
                'target_servers': ip_details.get('target_servers', []),
                'timestamp': django_timezone.now().isoformat()
            }
            
            return JsonResponse(formatted_details)
            
        except Exception as e:
            logger.error(f"IP Details API error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


# Global instance
ip_analyzer = IPAnalyzer()
