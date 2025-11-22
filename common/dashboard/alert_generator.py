"""
Real Alert Generator
Mevcut API'leri kullanarak gerçek sistem alertleri üretir
"""

import requests
import json
import logging
import subprocess  # nosec B404 - Used with safe, static arguments only
import shutil
from django.conf import settings
from django.utils import timezone
from .models import SystemAlert, SystemService

logger = logging.getLogger(__name__)

class RealAlertGenerator:
    """Mevcut API'leri kullanarak gerçek alertler üretir"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        self.thresholds = {
            'cpu_critical': 90,
            'cpu_warning': 80,
            'memory_critical': 90,
            'memory_warning': 80,
            'disk_critical': 95,
            'disk_warning': 85,
            'load_critical': 5.0,
            'load_warning': 3.0,
            'temperature_critical': 80,
            'temperature_warning': 70
        }
    
    def generate_all_alerts(self):
        """Tüm alert türlerini üretir"""
        alerts = []
        
        try:
            # Sistem metrikleri alertleri
            system_alerts = self._generate_system_metrics_alerts()
            alerts.extend(system_alerts)
            
            # Docker container alertleri
            docker_alerts = self._generate_docker_alerts()
            alerts.extend(docker_alerts)
            
            # Servis durumu alertleri
            service_alerts = self._generate_service_alerts()
            alerts.extend(service_alerts)
            
            logger.info(f"Generated {len(alerts)} alerts")
            
        except Exception as e:
            logger.error(f"Error generating alerts: {e}")
            # Hata durumunda en azından bir alert oluştur
            alerts.append({
                'alert_type': 'error',
                'title': 'Alert Generation Failed',
                'message': f'Failed to generate alerts: {str(e)}',
                'service': None
            })
        
        return alerts
    
    def _get_system_metrics(self):
        """Sistem metriklerini doğrudan alır"""
        try:
            import psutil
            import os
            from django.utils import timezone
            
            # CPU bilgileri
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory bilgileri
            memory = psutil.virtual_memory()
            memory_total = memory.total
            memory_used = memory.used
            memory_percent = memory.percent
            
            # Disk bilgileri
            disk = psutil.disk_usage('/')
            disk_total = disk.total
            disk_used = disk.used
            disk_percent = (disk.used / disk.total) * 100
            
            # Network bilgileri
            network = psutil.net_io_counters()
            network_in = network.bytes_recv
            network_out = network.bytes_sent
            
            # Load average (Linux only)
            try:
                load_avg = os.getloadavg()[0]
            except (AttributeError, OSError):
                # getloadavg not available on Windows or other systems
                load_avg = 0.0
            
            # Temperature (Linux only)
            temperature = None
            try:
                if os.path.exists('/sys/class/thermal/thermal_zone0/temp'):
                    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                        temp = int(f.read().strip()) / 1000
                        temperature = round(temp, 1)
            except (IOError, OSError, ValueError) as e:
                # Temperature sensor not available or invalid data
                temperature = None
            
            return {
                'success': True,
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': cpu_count,
                    'frequency': cpu_freq.current if cpu_freq else 0,
                    'temperature': temperature
                },
                'memory': {
                    'total': memory_total,
                    'used': memory_used,
                    'free': memory_total - memory_used,
                    'usage_percent': memory_percent
                },
                'disk': {
                    'total': disk_total,
                    'used': disk_used,
                    'free': disk_total - disk_used,
                    'usage_percent': disk_percent
                },
                'network': {
                    'bytes_in': network_in,
                    'bytes_out': network_out
                },
                'system': {
                    'load_average': load_avg
                }
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return None
    
    def _get_docker_containers(self):
        """Docker container bilgilerini doğrudan alır"""
        try:
            containers = []
            
            # Find full path to docker executable to prevent PATH hijacking
            docker_path = shutil.which('docker')
            if not docker_path:
                logger.warning("Docker executable not found in PATH")
                return {
                    'success': False,
                    'containers': [],
                    'error': 'Docker not found'
                }
            
            # Docker ps komutu - Security: Using full path and list format (not shell) with static arguments
            # Full path prevents PATH hijacking, arguments are static and not user-controlled
            result = subprocess.run(  # nosec B603 - Safe: full path, static args, shell=False
                [docker_path, 'ps', '-a', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,  # Explicitly set to False for security
                check=False   # We check returncode manually
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            container_data = json.loads(line)
                            containers.append({
                                'id': container_data.get('ID', '')[:12],
                                'name': container_data.get('Names', ''),
                                'image': container_data.get('Image', ''),
                                'status': container_data.get('State', ''),
                                'ports': container_data.get('Ports', ''),
                                'created': container_data.get('CreatedAt', ''),
                                'command': container_data.get('Command', '')
                            })
                        except json.JSONDecodeError:
                            continue
            
            return {
                'success': True,
                'containers': containers
            }
            
        except Exception as e:
            logger.error(f"Error getting docker containers: {e}")
            return None
    
    def _generate_system_metrics_alerts(self):
        """Sistem metriklerine göre alert üretir"""
        alerts = []
        
        # Sistem metriklerini doğrudan al
        data = self._get_system_metrics()
        if not data or not data.get('success'):
            return alerts
        
        metrics = data
        
        # CPU Alert
        cpu_usage = metrics.get('cpu', {}).get('usage_percent', 0)
        if cpu_usage >= self.thresholds['cpu_critical']:
            alerts.append({
                'alert_type': 'critical',
                'title': 'Critical CPU Usage',
                'message': f'CPU usage is {cpu_usage:.1f}% (Critical threshold: {self.thresholds["cpu_critical"]}%)',
                'service': self._get_or_create_service('system-cpu', 'System CPU', 'system')
            })
        elif cpu_usage >= self.thresholds['cpu_warning']:
            alerts.append({
                'alert_type': 'warning',
                'title': 'High CPU Usage',
                'message': f'CPU usage is {cpu_usage:.1f}% (Warning threshold: {self.thresholds["cpu_warning"]}%)',
                'service': self._get_or_create_service('system-cpu', 'System CPU', 'system')
            })
        
        # Memory Alert
        memory_usage = metrics.get('memory', {}).get('usage_percent', 0)
        if memory_usage >= self.thresholds['memory_critical']:
            alerts.append({
                'alert_type': 'critical',
                'title': 'Critical Memory Usage',
                'message': f'Memory usage is {memory_usage:.1f}% (Critical threshold: {self.thresholds["memory_critical"]}%)',
                'service': self._get_or_create_service('system-memory', 'System Memory', 'system')
            })
        elif memory_usage >= self.thresholds['memory_warning']:
            alerts.append({
                'alert_type': 'warning',
                'title': 'High Memory Usage',
                'message': f'Memory usage is {memory_usage:.1f}% (Warning threshold: {self.thresholds["memory_warning"]}%)',
                'service': self._get_or_create_service('system-memory', 'System Memory', 'system')
            })
        
        # Disk Alert
        disk_usage = metrics.get('disk', {}).get('usage_percent', 0)
        if disk_usage >= self.thresholds['disk_critical']:
            alerts.append({
                'alert_type': 'critical',
                'title': 'Critical Disk Usage',
                'message': f'Disk usage is {disk_usage:.1f}% (Critical threshold: {self.thresholds["disk_critical"]}%)',
                'service': self._get_or_create_service('system-disk', 'System Disk', 'system')
            })
        elif disk_usage >= self.thresholds['disk_warning']:
            alerts.append({
                'alert_type': 'warning',
                'title': 'High Disk Usage',
                'message': f'Disk usage is {disk_usage:.1f}% (Warning threshold: {self.thresholds["disk_warning"]}%)',
                'service': self._get_or_create_service('system-disk', 'System Disk', 'system')
            })
        
        # Load Average Alert
        load_avg = metrics.get('system', {}).get('load_average', 0)
        if load_avg >= self.thresholds['load_critical']:
            alerts.append({
                'alert_type': 'critical',
                'title': 'Critical System Load',
                'message': f'System load average is {load_avg:.2f} (Critical threshold: {self.thresholds["load_critical"]})',
                'service': self._get_or_create_service('system-load', 'System Load', 'system')
            })
        elif load_avg >= self.thresholds['load_warning']:
            alerts.append({
                'alert_type': 'warning',
                'title': 'High System Load',
                'message': f'System load average is {load_avg:.2f} (Warning threshold: {self.thresholds["load_warning"]})',
                'service': self._get_or_create_service('system-load', 'System Load', 'system')
            })
        
        # Temperature Alert
        temperature = metrics.get('cpu', {}).get('temperature')
        if temperature and temperature >= self.thresholds['temperature_critical']:
            alerts.append({
                'alert_type': 'critical',
                'title': 'Critical CPU Temperature',
                'message': f'CPU temperature is {temperature}°C (Critical threshold: {self.thresholds["temperature_critical"]}°C)',
                'service': self._get_or_create_service('system-temperature', 'System Temperature', 'system')
            })
        elif temperature and temperature >= self.thresholds['temperature_warning']:
            alerts.append({
                'alert_type': 'warning',
                'title': 'High CPU Temperature',
                'message': f'CPU temperature is {temperature}°C (Warning threshold: {self.thresholds["temperature_warning"]}°C)',
                'service': self._get_or_create_service('system-temperature', 'System Temperature', 'system')
            })
        
        return alerts
    
    def _generate_docker_alerts(self):
        """Docker container durumuna göre alert üretir"""
        alerts = []
        
        # Docker container bilgilerini doğrudan al
        data = self._get_docker_containers()
        if not data or not data.get('success'):
            return alerts
        
        containers = data.get('containers', [])
        
        # Stopped containers alert
        stopped_containers = [c for c in containers if c.get('status') == 'exited']
        if stopped_containers:
            container_names = [c.get('name', c.get('id', 'Unknown')) for c in stopped_containers]
            alerts.append({
                'alert_type': 'warning',
                'title': 'Stopped Docker Containers',
                'message': f'{len(stopped_containers)} containers are stopped: {", ".join(container_names[:3])}{"..." if len(container_names) > 3 else ""}',
                'service': self._get_or_create_service('docker', 'Docker', 'docker')
            })
        
        # No running containers alert (if there should be some)
        running_containers = [c for c in containers if c.get('status') == 'running']
        if not running_containers and len(containers) > 0:
            alerts.append({
                'alert_type': 'warning',
                'title': 'No Running Docker Containers',
                'message': 'No Docker containers are currently running',
                'service': self._get_or_create_service('docker', 'Docker', 'docker')
            })
        
        # Container count alert
        total_containers = len(containers)
        if total_containers > 20:  # Çok fazla container varsa
            alerts.append({
                'alert_type': 'info',
                'title': 'High Container Count',
                'message': f'System has {total_containers} Docker containers (consider cleanup)',
                'service': self._get_or_create_service('docker', 'Docker', 'docker')
            })
        
        return alerts
    
    def _generate_service_alerts(self):
        """Kritik servislerin durumuna göre alert üretir"""
        alerts = []
        
        # Kritik servisler listesi
        critical_services = [
            'docker', 'systemd', 'systemd-networkd', 'ssh', 'dbus',
            'systemd-logind', 'systemd-resolved'
        ]
        
        for service_name in critical_services:
            try:
                service = SystemService.objects.get(name=service_name)
                
                # Servis durumu kontrolü
                if service.status == 'failed':
                    alerts.append({
                        'alert_type': 'critical',
                        'title': f'{service.display_name} Service Failed',
                        'message': f'{service.display_name} service has failed and needs immediate attention',
                        'service': service
                    })
                elif service.status == 'inactive':
                    alerts.append({
                        'alert_type': 'warning',
                        'title': f'{service.display_name} Service Inactive',
                        'message': f'{service.display_name} service is inactive',
                        'service': service
                    })
                elif service.status == 'unknown':
                    alerts.append({
                        'alert_type': 'info',
                        'title': f'{service.display_name} Service Status Unknown',
                        'message': f'Cannot determine status of {service.display_name} service',
                        'service': service
                    })
                
                # Error count kontrolü
                if service.error_count > 10:
                    alerts.append({
                        'alert_type': 'warning',
                        'title': f'{service.display_name} High Error Count',
                        'message': f'{service.display_name} has {service.error_count} errors',
                        'service': service
                    })
                
            except SystemService.DoesNotExist:
                # Servis veritabanında yoksa uyarı ver
                alerts.append({
                    'alert_type': 'info',
                    'title': f'Service {service_name} Not Monitored',
                    'message': f'{service_name} service is not being monitored',
                    'service': None
                })
        
        return alerts
    
    def _get_or_create_service(self, name, display_name, category):
        """Servis oluşturur veya mevcut olanı döndürür"""
        try:
            service, created = SystemService.objects.get_or_create(
                name=name,
                defaults={
                    'display_name': display_name,
                    'category': category,
                    'status': 'active',
                    'is_critical': True
                }
            )
            return service
        except Exception as e:
            logger.error(f"Error creating service {name}: {e}")
            return None
    
    def save_alerts(self, alerts):
        """Alertleri veritabanına kaydeder"""
        saved_count = 0
        
        for alert_data in alerts:
            try:
                # Aynı alert'in zaten var olup olmadığını kontrol et
                existing_alert = SystemAlert.objects.filter(
                    title=alert_data['title'],
                    is_resolved=False,
                    created_at__gte=timezone.now() - timezone.timedelta(minutes=5)
                ).first()
                
                if not existing_alert:
                    SystemAlert.objects.create(
                        alert_type=alert_data['alert_type'],
                        title=alert_data['title'],
                        message=alert_data['message'],
                        service=alert_data.get('service'),
                        metadata={
                            'generated_by': 'RealAlertGenerator',
                            'timestamp': timezone.now().isoformat()
                        }
                    )
                    saved_count += 1
                    
            except Exception as e:
                logger.error(f"Error saving alert {alert_data.get('title', 'Unknown')}: {e}")
        
        logger.info(f"Saved {saved_count} new alerts")
        return saved_count
