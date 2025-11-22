"""
Dashboard Views
Gerçek sistem bilgilerini döndüren API endpoint'leri
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.cache import cache
import subprocess  # nosec B404 - Used with safe, static arguments only
import psutil
import os
import json
import logging
import shutil
from datetime import datetime, timedelta

from .models import SystemService, SystemAlert, SystemActivity, SystemMetrics, DashboardSettings

logger = logging.getLogger(__name__)

# Import SMTP models if available
try:
    from common.smtp.models import SMTPConfig, EmailAutomation
    SMTP_AVAILABLE = True
except ImportError:
    SMTP_AVAILABLE = False


@login_required
def dashboard_overview(request):
    """Dashboard ana sayfası"""
    return render(request, 'pages/dashboard.html')


@login_required
@require_http_methods(["GET"])
def get_system_metrics(request):
    """Gerçek sistem metriklerini döndür"""
    try:
        # Cache kontrolü (5 saniye)
        cached_data = cache.get('system_metrics')
        if cached_data:
            return JsonResponse(cached_data)
        
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
        
        # Sistem bilgileri
        boot_time = psutil.boot_time()
        uptime_seconds = timezone.now().timestamp() - boot_time
        uptime_days = int(uptime_seconds // 86400)
        uptime_hours = int((uptime_seconds % 86400) // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)
        
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
        
        # Metrics'i veritabanına kaydet
        SystemMetrics.objects.create(
            cpu_usage=cpu_percent,
            memory_usage=memory_percent,
            memory_total=memory_total,
            memory_used=memory_used,
            disk_usage=disk_percent,
            disk_total=disk_total,
            disk_used=disk_used,
            network_in=network_in,
            network_out=network_out,
            temperature=temperature,
            uptime=int(uptime_seconds),
            load_average=load_avg
        )
        
        # Eski metrics'leri temizle (24 saatten eski)
        old_metrics = SystemMetrics.objects.filter(
            timestamp__lt=timezone.now() - timedelta(hours=24)
        )
        old_metrics.delete()
        
        data = {
            'success': True,
            'timestamp': timezone.now().isoformat(),
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
                'bytes_out': network_out,
                'speed': 0  # Bu değer hesaplanabilir
            },
            'system': {
                'uptime': f"{uptime_days}d {uptime_hours}h {uptime_minutes}m",
                'uptime_seconds': int(uptime_seconds),
                'load_average': load_avg,
                'boot_time': datetime.fromtimestamp(boot_time).isoformat()
            }
        }
        
        # Cache'e kaydet (5 saniye)
        cache.set('system_metrics', data, 5)
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)




@login_required
@require_http_methods(["GET"])
def get_docker_containers(request):
    """Docker container bilgilerini döndür"""
    try:
        # Cache kontrolü (15 saniye)
        cached_data = cache.get('docker_containers')
        if cached_data:
            return JsonResponse(cached_data)
        
        containers = []
        
        try:
            # Find full path to docker executable to prevent PATH hijacking
            docker_path = shutil.which('docker')
            if not docker_path:
                logger.warning("Docker executable not found in PATH")
                return JsonResponse({
                    'success': False,
                    'containers': [],
                    'error': 'Docker not found'
                })
            
            # Docker ps komutu - Security: Using full path and list format (not shell) with static arguments
            result = subprocess.run(  # nosec B603, B607 - Safe: full path, static args, shell=False
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
        
        except subprocess.TimeoutExpired:
            logger.warning("docker ps command timed out")
        except Exception as e:
            logger.error(f"Error checking docker containers: {e}")
        
        # Özet bilgiler
        running = len([c for c in containers if c['status'] == 'running'])
        stopped = len([c for c in containers if c['status'] == 'exited'])
        
        data = {
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'containers': containers,
            'total': len(containers),
            'running': running,
            'stopped': stopped
        }
        
        # Cache'e kaydet (15 saniye)
        cache.set('docker_containers', data, 15)
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error getting docker containers: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_alerts(request):
    """Sistem uyarılarını döndür ve gerçek alertler üret"""
    try:
        # Gerçek alert üretimi (her 30 saniyede bir)
        from .alert_generator import RealAlertGenerator
        from django.core.cache import cache
        
        # Cache kontrolü - 30 saniyede bir alert üret
        cache_key = 'last_alert_generation'
        last_generation = cache.get(cache_key)
        now = timezone.now()
        
        if not last_generation or (now - last_generation).seconds >= 30:
            try:
                generator = RealAlertGenerator()
                new_alerts = generator.generate_all_alerts()
                generator.save_alerts(new_alerts)
                cache.set(cache_key, now, 30)
                logger.info(f"Generated {len(new_alerts)} real alerts")
            except Exception as e:
                logger.error(f"Error generating real alerts: {e}")
        
        # Mevcut alertleri getir
        settings = DashboardSettings.get_settings()
        alerts = SystemAlert.objects.filter(
            is_resolved=False
        ).order_by('-created_at')[:settings.max_alerts]
        
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                'id': alert.id,
                'type': alert.alert_type,
                'title': alert.title,
                'message': alert.message,
                'service': alert.service.display_name if alert.service else None,
                'created_at': alert.created_at.isoformat(),
                'icon': alert.get_alert_icon()
            })
        
        return JsonResponse({
            'success': True,
            'alerts': alerts_data,
            'total': len(alerts_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def resolve_alert(request, alert_id):
    """Alert'i çözüldü olarak işaretle"""
    try:
        alert = SystemAlert.objects.get(id=alert_id)
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Alert resolved successfully'
        })
        
    except SystemAlert.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Alert not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def unresolve_alert(request, alert_id):
    """Alert'i çözülmemiş olarak işaretle"""
    try:
        alert = SystemAlert.objects.get(id=alert_id)
        alert.is_resolved = False
        alert.resolved_at = None
        alert.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Alert marked as unresolved'
        })
        
    except SystemAlert.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Alert not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error unresolving alert {alert_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_alert_statistics(request):
    """Alert istatistiklerini döndür"""
    try:
        stats = {
            'total': SystemAlert.objects.count(),
            'unresolved': SystemAlert.objects.filter(is_resolved=False).count(),
            'critical': SystemAlert.objects.filter(alert_type='critical', is_resolved=False).count(),
            'warning': SystemAlert.objects.filter(alert_type='warning', is_resolved=False).count(),
            'error': SystemAlert.objects.filter(alert_type='error', is_resolved=False).count(),
            'info': SystemAlert.objects.filter(alert_type='info', is_resolved=False).count(),
        }
        
        return JsonResponse({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting alert statistics: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_activities(request):
    """Sistem aktivitelerini döndür"""
    try:
        settings = DashboardSettings.get_settings()
        activities = SystemActivity.objects.all().order_by('-created_at')[:settings.max_activities]
        
        activities_data = []
        for activity in activities:
            activities_data.append({
                'id': activity.id,
                'type': activity.activity_type,
                'title': activity.title,
                'description': activity.description,
                'user': activity.user.username if activity.user else 'System',
                'service': activity.service.display_name if activity.service else None,
                'created_at': activity.created_at.isoformat(),
                'icon': activity.get_activity_icon()
            })
        
        return JsonResponse({
            'success': True,
            'activities': activities_data,
            'total': len(activities_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting activities: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_dashboard_data(request):
    """Tüm dashboard verilerini tek seferde döndür"""
    try:
        # Cache kontrolü (5 saniye)
        cached_data = cache.get('dashboard_data')
        if cached_data:
            return JsonResponse(cached_data)
        
        # Tüm verileri topla
        data = {
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'system_metrics': None,
            'services': [],
            'containers': [],
            'alerts': [],
            'activities': []
        }
        
        # Sistem metrikleri
        try:
            metrics_response = get_system_metrics(request)
            if metrics_response.status_code == 200:
                data['system_metrics'] = json.loads(metrics_response.content)
        except (AttributeError, json.JSONDecodeError, Exception) as e:
            # API call failed or invalid response - continue without metrics
            logger.debug(f"Failed to get system metrics: {e}")
        
        # Docker containers
        try:
            containers_response = get_docker_containers(request)
            if containers_response.status_code == 200:
                containers_data = json.loads(containers_response.content)
                data['containers'] = containers_data.get('containers', [])
        except (AttributeError, json.JSONDecodeError, Exception) as e:
            # API call failed or invalid response - continue without containers
            logger.debug(f"Failed to get docker containers: {e}")
        
        # Alerts
        try:
            alerts_response = get_alerts(request)
            if alerts_response.status_code == 200:
                alerts_data = json.loads(alerts_response.content)
                data['alerts'] = alerts_data.get('alerts', [])
        except (AttributeError, json.JSONDecodeError, Exception) as e:
            # API call failed or invalid response - continue without alerts
            logger.debug(f"Failed to get alerts: {e}")
        
        # Activities
        try:
            activities_response = get_activities(request)
            if activities_response.status_code == 200:
                activities_data = json.loads(activities_response.content)
                data['activities'] = activities_data.get('activities', [])
        except (AttributeError, json.JSONDecodeError, Exception) as e:
            # API call failed or invalid response - continue without activities
            logger.debug(f"Failed to get activities: {e}")
        
        # Cache'e kaydet (5 saniye)
        cache.set('dashboard_data', data, 5)
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_redis_celery_status(request):
    """Get Redis and Celery connection status"""
    try:
        redis_status = {
            'connected': False,
            'host': 'localhost',
            'port': 6379,
            'error': None
        }
        
        celery_status = {
            'connected': False,
            'workers_active': 0,
            'error': None
        }
        
        # Check Redis connection
        try:
            import redis
            from django.conf import settings
            
            # Try to connect to Redis
            redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            
            # Test connection with ping
            redis_client.ping()
            redis_status['connected'] = True
            redis_status['host'] = 'localhost'
            redis_status['port'] = 6379
            
        except redis.ConnectionError as e:
            redis_status['connected'] = False
            redis_status['error'] = 'Connection failed'
            logger.debug(f"Redis connection error: {e}")
        except ImportError:
            redis_status['connected'] = False
            redis_status['error'] = 'Redis library not available'
        except Exception as e:
            redis_status['connected'] = False
            redis_status['error'] = str(e)
            logger.debug(f"Redis check error: {e}")
        
        # Check Celery connection
        try:
            from celery import current_app
            from celery.result import AsyncResult
            
            # Get active workers
            inspect = current_app.control.inspect()
            active_workers = inspect.active()
            
            if active_workers:
                celery_status['connected'] = True
                celery_status['workers_active'] = len(active_workers)
            else:
                # Try to check if Celery is configured
                celery_status['connected'] = False
                celery_status['error'] = 'No active workers'
                
        except Exception as e:
            celery_status['connected'] = False
            celery_status['error'] = str(e)
            logger.debug(f"Celery check error: {e}")
        
        return JsonResponse({
            'success': True,
            'redis': redis_status,
            'celery': celery_status
        })
        
    except Exception as e:
        logger.error(f"Error getting Redis/Celery status: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_smtp_status(request):
    """Get SMTP configuration and CVE automation status"""
    try:
        if not SMTP_AVAILABLE:
            return JsonResponse({
                'success': True,
                'smtp': {
                    'configured': False,
                    'is_active': False,
                    'test_success': None,
                    'host': None,
                    'from_email': None
                },
                'cve_automation': {
                    'enabled': False,
                    'live': False
                }
            })
        
        # Get SMTP config
        smtp_config = SMTPConfig.objects.first()
        
        smtp_data = {
            'configured': smtp_config is not None,
            'is_active': smtp_config.is_active if smtp_config else False,
            'test_success': smtp_config.last_test_success if smtp_config else None,
            'host': smtp_config.host if smtp_config else None,
            'from_email': (smtp_config.from_email or smtp_config.username) if smtp_config else None
        }
        
        # Get CVE automation status
        cve_automation = EmailAutomation.objects.filter(
            automation_type='cve',
            is_enabled=True
        ).first()
        
        cve_data = {
            'enabled': cve_automation is not None,
            'live': cve_automation.is_enabled if cve_automation else False,
            'name': cve_automation.name if cve_automation else None,
            'last_run_at': cve_automation.last_run_at.isoformat() if cve_automation and cve_automation.last_run_at else None,
            'last_run_status': cve_automation.last_run_status if cve_automation else None
        }
        
        return JsonResponse({
            'success': True,
            'smtp': smtp_data,
            'cve_automation': cve_data
        })
        
    except Exception as e:
        logger.error(f"Error getting SMTP status: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)