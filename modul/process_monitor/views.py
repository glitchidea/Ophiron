"""
Process Monitor Views
Ağ süreçlerini izlemek için view fonksiyonları
"""

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.conf import settings as django_settings
from .utils import process_monitor, process_manager
from .models import ProcessMonitorCache, ProcessMonitorSettings
from .ip_analyzer import ip_analyzer
from .pdf_generator import ProcessMonitorPDFGenerator
from .pid_grouper import pid_grouper
import logging
import os
from datetime import datetime
from functools import wraps
import json

logger = logging.getLogger(__name__)

# Process Monitor logger
PM_LOG_DIR = os.path.join('logger', 'process-monitor')
os.makedirs(PM_LOG_DIR, exist_ok=True)

def get_pm_logger():
    """Get daily rotating Process Monitor logger"""
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(PM_LOG_DIR, f'process_monitor_{today}.log')
    
    pm_logger = logging.getLogger('process_monitor_api')
    pm_logger.setLevel(logging.INFO)
    
    # Remove old handlers
    pm_logger.handlers = []
    
    # Create file handler
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    
    pm_logger.addHandler(fh)
    
    return pm_logger

def log_process_monitor_request(func):
    """Decorator to log Process Monitor API requests"""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        # Check if logging is enabled
        settings = ProcessMonitorSettings.get_global_settings()
        
        if settings.logging_enabled:
            pm_logger = get_pm_logger()
            
            # Log request start
            user = request.user.username if request.user.is_authenticated else 'Anonymous'
            endpoint = request.path
            method = request.method
            
            # Log request details
            log_data = {
                'user': user,
                'ip': request.META.get('REMOTE_ADDR'),
                'method': method,
                'endpoint': endpoint,
                'args': str(args) if args else None,
                'kwargs': str(kwargs) if kwargs else None
            }
            
            pm_logger.info(f"REQUEST | {user} | {method} {endpoint} | {json.dumps(log_data, ensure_ascii=False)}")
            
            # Execute function
            try:
                response = func(request, *args, **kwargs)
                
                # Log response
                if isinstance(response, JsonResponse):
                    try:
                        response_data = json.loads(response.content.decode('utf-8'))
                        success = response_data.get('success', False)
                        status = 'SUCCESS' if success else 'FAILED'
                        pm_logger.info(f"RESPONSE | {user} | {status} | {method} {endpoint}")
                    except:
                        pm_logger.info(f"RESPONSE | {user} | {method} {endpoint}")
                
                return response
                
            except Exception as e:
                pm_logger.error(f"ERROR | {user} | {method} {endpoint} | {str(e)}")
                raise
        else:
            # If logging disabled, just execute function
            return func(request, *args, **kwargs)
    
    return wrapper


@login_required
def process_monitor_view(request):
    """Process Monitor ana sayfası (Cache-First Loading)"""
    try:
        # Global ayarları kontrol et
        settings = ProcessMonitorSettings.get_global_settings()
        
        connections = []
        
        if settings.live_mode_enabled:
            # Live mode AÇIKSA → Cache'ten oku (ANINDA!)
            logger.info("🚀 Live mode açık, cache'ten yükleniyor...")
            
            # Önce Redis cache'ten dene
            connections = cache.get('process_monitor:connections')
            
            # Redis'te yoksa Database cache'ten dene
            if connections is None:
                connections = ProcessMonitorCache.get_cache('connections')
                logger.info("📦 Database cache'ten yüklendi")
            else:
                logger.info("⚡ Redis cache'ten yüklendi")
            
            # Cache tamamen boşsa (ilk kullanım)
            if connections is None:
                logger.warning("⚠️ Cache boş! İlk veri çekiliyor...")
                connections = process_monitor.get_network_connections()
                # Cache'e yaz (bir sonraki için)
                cache.set('process_monitor:connections', connections, timeout=60)
                ProcessMonitorCache.set_cache('connections', connections, duration=60)
        else:
            # Live mode KAPALI → Gerçek zamanlı çek (Normal)
            logger.info("🔄 Live mode kapalı, gerçek zamanlı veri çekiliyor...")
            connections = process_monitor.get_network_connections()
        
        import json
        return render(request, 'modules/process_monitor/index.html', {
            'connections': connections or [],
            'connections_json': json.dumps(connections or []),
            'live_mode_enabled': settings.live_mode_enabled
        })
    except Exception as e:
        logger.error(f"❌ Process monitor sayfası yüklenirken hata: {str(e)}")
        import json
        return render(request, 'modules/process_monitor/index.html', {
            'error': str(e),
            'connections': [],
            'connections_json': json.dumps([]),
            'live_mode_enabled': False
        })


@login_required
def get_connections_api(request):
    """Ağ bağlantılarını JSON olarak döndür (Cache'ten)"""
    try:
        # Önce Redis cache'ten dene
        connections = cache.get('process_monitor:connections')
        
        # Cache'te yoksa database cache'ten dene
        if connections is None:
            connections = ProcessMonitorCache.get_cache('connections')
        
        # Hala yoksa gerçek zamanlı çek
        if connections is None:
            logger.warning("Cache boş, gerçek zamanlı veri çekiliyor...")
            connections = process_monitor.get_network_connections()
        
        return JsonResponse({
            'success': True,
            'connections': connections,
            'cached': connections is not None
        })
    except Exception as e:
        logger.error(f"Bağlantılar alınırken hata: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def get_grouped_processes_api(request):
    """Gruplu süreçleri JSON olarak döndür"""
    try:
        processes = process_monitor.get_grouped_processes()
        return JsonResponse({
            'success': True,
            'processes': processes
        })
    except Exception as e:
        logger.error(f"Gruplu süreçler alınırken hata: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@log_process_monitor_request
def get_pid_grouped_processes_api(request):
    """PID'e göre gruplu süreçleri JSON olarak döndür"""
    try:
        # Önce cache'ten bağlantıları al
        connections = cache.get('process_monitor:connections')
        
        if connections is None:
            connections = ProcessMonitorCache.get_cache('connections')
        
        if connections is None:
            logger.warning("Cache boş, gerçek zamanlı veri çekiliyor...")
            connections = process_monitor.get_network_connections()
        
        # PID'e göre grupla (pid_grouper modülünü kullan)
        grouped_processes = pid_grouper.group_by_pid(connections)
        
        # İstatistikleri hesapla
        statistics = pid_grouper.get_statistics(grouped_processes)
        
        return JsonResponse({
            'success': True,
            'processes': grouped_processes,
            'total_pids': len(grouped_processes),
            'statistics': statistics
        })
        
    except Exception as e:
        logger.error(f"PID'e göre süreçler alınırken hata: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def get_interfaces_api(request):
    """Ağ arayüzlerine göre süreçleri JSON olarak döndür"""
    try:
        interfaces = process_monitor.get_processes_by_interface()
        return JsonResponse({
            'success': True,
            'interfaces': interfaces
        })
    except Exception as e:
        logger.error(f"Arayüzlere göre süreçler alınırken hata: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def get_most_used_ports_api(request):
    """En çok kullanılan portları JSON olarak döndür (Cache'ten)"""
    try:
        limit = request.GET.get('limit', 6)
        try:
            limit = int(limit)
        except ValueError:
            limit = 6
        
        # Önce Redis cache'ten dene
        ports = cache.get('process_monitor:ports')
        
        # Cache'te yoksa database cache'ten dene
        if ports is None:
            ports = ProcessMonitorCache.get_cache('ports')
        
        # Hala yoksa gerçek zamanlı çek
        if ports is None:
            logger.warning("Port cache boş, gerçek zamanlı veri çekiliyor...")
            ports = process_monitor.get_most_used_ports(limit=limit)
        
        # Limit'e göre filtrele (çok büyük limitler için tümünü döndür)
        # Eğer limit 1000'den büyükse, cache'ten gelen verileri kullanma, gerçek zamanlı çek
        if limit >= 1000:
            logger.info(f"Large limit requested ({limit}), fetching real-time data...")
            ports = process_monitor.get_most_used_ports(limit=limit)
        elif ports and len(ports) > limit:
            ports = ports[:limit]
        
        return JsonResponse({
            'success': True,
            'ports': ports or [],
            'cached': ports is not None,
            'total_ports': len(ports) if ports else 0
        })
    except Exception as e:
        logger.error(f"Portlar alınırken hata: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def get_port_details_api(request, port):
    """Belirli bir port için detayları döndür"""
    try:
        details = process_monitor.get_port_details(port)
        if details:
            return JsonResponse({
                'success': True,
                'data': details
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Port bilgisi bulunamadı'
            }, status=404)
    except Exception as e:
        logger.error(f"Port detayları alınırken hata: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
def get_process_details_api(request, pid):
    """Belirli bir sürecin detaylarını döndür"""
    try:
        details = process_monitor.get_detailed_process_info(int(pid))
        if details:
            return JsonResponse({
                'success': True,
                'data': details
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Süreç bulunamadı'
            }, status=404)
    except Exception as e:
        logger.error(f"Süreç detayları alınırken hata: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@log_process_monitor_request
def manage_process_api(request, pid, action):
    """Süreç yönetim işlemlerini gerçekleştir"""
    try:
        pid = int(pid)
        
        # Aksiyonu gerçekleştir
        if action == 'stop':
            result = process_manager.terminate_process(pid)
        elif action == 'kill':
            result = process_manager.kill_process(pid)
        elif action == 'suspend':
            result = process_manager.suspend_process(pid)
        elif action == 'resume':
            result = process_manager.resume_process(pid)
        elif action == 'restart':
            # Önce terminate sonra start (basit versiyonu)
            result = process_manager.terminate_process(pid)
        else:
            return JsonResponse({
                'success': False,
                'message': 'Geçersiz aksiyon'
            }, status=400)
        
        return JsonResponse(result)
    
    except ValueError:
        return JsonResponse({
            'success': False,
            'message': 'Geçersiz PID'
        }, status=400)
    except Exception as e:
        logger.error(f"Süreç yönetimi sırasında hata: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


# ========================
# SERVICE MANAGEMENT APIs
# ========================

@login_required
def get_service_status_api(request):
    """Live mode ve background service durumunu getir (Admin-only)"""
    # Sadece superuser erişebilir
    if not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'error': 'Unauthorized: Admin access required'
        }, status=403)
    
    try:
        settings = ProcessMonitorSettings.get_global_settings()
        
        # Cache durumunu kontrol et
        cached_connections = cache.get('process_monitor:connections')
        cached_ports = cache.get('process_monitor:ports')
        
        return JsonResponse({
            'success': True,
            'live_mode_enabled': settings.live_mode_enabled,
            'background_service_enabled': settings.background_service_enabled,
            'monitoring_interval': settings.monitoring_interval,
            'cache_duration': settings.cache_duration,
            'realtime_websocket_enabled': settings.realtime_websocket_enabled,
            'logging_enabled': settings.logging_enabled,
            'last_modified_by': settings.last_modified_by or 'N/A',
            'cache_status': {
                'connections': cached_connections is not None,
                'ports': cached_ports is not None,
            }
        })
    except Exception as e:
        logger.error(f"Service status alınırken hata: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@log_process_monitor_request
def toggle_live_mode_api(request):
    """Live mode'u aç/kapa (Admin-only, Global)"""
    # Sadece superuser erişebilir
    if not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'error': 'Unauthorized: Admin access required'
        }, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        enabled = data.get('enabled', False)
        
        # Global ayarları güncelle
        settings = ProcessMonitorSettings.get_global_settings()
        settings.live_mode_enabled = enabled
        settings.background_service_enabled = enabled
        settings.last_modified_by = request.user.username
        settings.save()
        
        # Celery task'ını tetikle
        if enabled:
            from .tasks import update_process_monitor_cache
            update_process_monitor_cache.delay()
            logger.info(f"✓ Live mode ENABLED: {request.user.username} (Global)")
        else:
            logger.info(f"✗ Live mode DISABLED: {request.user.username} (Global)")
        
        return JsonResponse({
            'success': True,
            'live_mode_enabled': enabled,
            'message': f'Live mode {"enabled" if enabled else "disabled"} (Global for all admins)'
        })
    except Exception as e:
        logger.error(f"Live mode toggle hatası: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@log_process_monitor_request
def update_monitoring_settings_api(request):
    """Monitoring ayarlarını güncelle (Admin-only, Global)"""
    # Sadece superuser erişebilir
    if not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'error': 'Unauthorized: Admin access required'
        }, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        
        settings = ProcessMonitorSettings.get_global_settings()
        
        # Monitoring interval (0.5 - 10.0 arası)
        if 'monitoring_interval' in data:
            interval = float(data['monitoring_interval'])
            if 0.5 <= interval <= 10.0:
                settings.monitoring_interval = interval
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Interval must be between 0.5 and 10.0 seconds'
                }, status=400)
        
        # Cache duration (30 - 600 arası)
        if 'cache_duration' in data:
            cache_duration = int(data['cache_duration'])
            if 30 <= cache_duration <= 600:
                settings.cache_duration = cache_duration
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Cache duration must be between 30 and 600 seconds'
                }, status=400)
        
        # Realtime WebSocket
        if 'realtime_websocket_enabled' in data:
            settings.realtime_websocket_enabled = bool(data['realtime_websocket_enabled'])
        
        # Logging
        if 'logging_enabled' in data:
            settings.logging_enabled = bool(data['logging_enabled'])
        
        settings.last_modified_by = request.user.username
        settings.save()
        
        # Celery Beat'i yeniden başlat (interval değiştiğinde)
        # NOT: Bu otomatik olarak celerybeat-schedule dosyasından okunur
        
        logger.info(f"⚙️ Ayarlar güncellendi: {request.user.username} | Interval: {settings.monitoring_interval}s")
        
        return JsonResponse({
            'success': True,
            'message': 'Settings updated successfully (Global for all admins)',
            'settings': {
                'monitoring_interval': settings.monitoring_interval,
                'cache_duration': settings.cache_duration,
                'realtime_websocket_enabled': settings.realtime_websocket_enabled
            }
        })
    except Exception as e:
        logger.error(f"Ayarlar güncellenirken hata: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@log_process_monitor_request
def force_cache_update_api(request):
    """Cache'i manuel olarak güncelle"""
    try:
        from .tasks import update_process_monitor_cache
        task = update_process_monitor_cache.delay()
        
        return JsonResponse({
            'success': True,
            'message': 'Cache güncelleme başlatıldı',
            'task_id': task.id
        })
    except Exception as e:
        logger.error(f"Cache güncelleme hatası: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@log_process_monitor_request
def search_connections_api(request):
    """
    Search connections by PID, Port, or IP address
    Returns detailed information about matching connections
    """
    try:
        # Get search parameters
        search_type = request.GET.get('type', '').lower()  # pid, port, or ip
        search_value = request.GET.get('value', '').strip()
        
        # Validate parameters
        if not search_type or not search_value:
            return JsonResponse({
                'success': False,
                'error': 'Missing search parameters. Please provide both type and value.'
            }, status=400)
        
        if search_type not in ['pid', 'port', 'ip']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid search type. Must be one of: pid, port, ip'
            }, status=400)
        
        # Perform search
        results = process_monitor.search_connections(search_type, search_value)
        
        # Check for errors
        if 'error' in results:
            return JsonResponse({
                'success': False,
                'error': results['error']
            }, status=500)
        
        # Check if any results found
        if results['total_connections'] == 0:
            return JsonResponse({
                'success': True,
                'found': False,
                'message': f'No connections found for {search_type}: {search_value}',
                'search_type': search_type,
                'search_value': search_value
            })
        
        # Return successful results
        return JsonResponse({
            'success': True,
            'found': True,
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Connection search error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def download_search_report(request):
    """
    Download search results as a professional PDF report
    """
    try:
        # Get search parameters from request
        search_type = request.GET.get('type', '').lower()
        search_value = request.GET.get('value', '').strip()
        report_type = request.GET.get('report_type', 'simple').lower()
        
        if not search_type or not search_value:
            return JsonResponse({
                'success': False,
                'error': 'Missing search parameters'
            }, status=400)
        
        # Perform search
        results = process_monitor.search_connections(search_type, search_value)
        
        if 'error' in results:
            return JsonResponse({
                'success': False,
                'error': results['error']
            }, status=500)
        
        # Choose PDF generator based on report type
        if report_type == 'detailed':
            from .detailed_pdf_generator import DetailedProcessMonitorPDFGenerator
            pdf_generator = DetailedProcessMonitorPDFGenerator()
        else:
            pdf_generator = ProcessMonitorPDFGenerator()
        
        buffer = pdf_generator.generate_pdf(
            search_results=results,
            search_type=search_type,
            search_value=search_value,
            username=request.user.username
        )
        
        # Create filename with report type
        report_type_suffix = '_Detailed' if report_type == 'detailed' else '_Simple'
        filename = f"ProcessMonitor_Report_{search_type}_{search_value}{report_type_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Create HTTP response
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        logger.info(f"PDF Report downloaded: {filename} by {request.user.username} (Type: {report_type})")
        
        return response
        
    except Exception as e:
        logger.error(f"PDF Report generation error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def get_ip_analysis_api(request):
    """IP analizi için tüm IP adreslerini döndür"""
    return ip_analyzer.get_ip_analysis_api(request)


@login_required
def get_ip_details_api(request):
    """Belirli bir IP için detaylı analiz döndür"""
    return ip_analyzer.get_ip_details_api(request)



