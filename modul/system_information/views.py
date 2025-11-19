"""
System Information Views
Sistem bilgileri görüntüleme ve API endpoint'leri
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
import json

from .utils import system_info_collector
from .cache import SystemInfoCache
from .tasks import update_system_metrics, set_monitoring_interval, set_cache_duration
from .models import SystemInformationSettings, SystemInformationLog
import logging

logger = logging.getLogger(__name__)

def log_system_operation(operation_type, status, message, user='Anonymous', ip_address=None, execution_time=None, details=None):
    """Log System Information operations to database"""
    try:
        settings = SystemInformationSettings.get_global_settings()
        if settings.logging_enabled:
            SystemInformationLog.objects.create(
                operation_type=operation_type,
                status=status,
                message=message,
                user=user,
                ip_address=ip_address,
                execution_time=execution_time,
                details=details or {}
            )
            logger.info(f"System Information operation logged: {operation_type} - {status}")
    except Exception as e:
        logger.error(f"Failed to log System Information operation: {e}")


@login_required
def system_information_view(request):
    """
    Sistem bilgileri ana sayfası
    """
    try:
        # Check if live mode is enabled and cache is empty
        settings = SystemInformationSettings.get_global_settings()
        if settings.live_mode_enabled:
            cached_data = SystemInfoCache.get_all_metrics()
            if cached_data is None:
                logger.info("Live mode enabled but no cached data, updating cache...")
                result = update_system_metrics()
                if result.get('success'):
                    logger.info("Cache updated successfully for live mode")
                else:
                    logger.error(f"Failed to update cache: {result.get('error')}")
        
        # Tüm sistem bilgilerini topla
        system_data = system_info_collector.get_all_system_info()
        
        context = {
            'cpu_info': system_data.get('cpu', {}),
            'memory_info': system_data.get('memory', {}),
            'disk_info': system_data.get('disk', {}).get('partitions', []),
            'disk_summary': {
                'total_space': system_data.get('disk', {}).get('total_space', 0),
                'used_space': system_data.get('disk', {}).get('used_space', 0),
                'free_space': system_data.get('disk', {}).get('free_space', 0),
                'total_percent': system_data.get('disk', {}).get('total_percent', 0)
            },
            'network_info': system_data.get('network', {}),
            'os_info': system_data.get('os', {}),
            'users': system_data.get('users', []),
            'security': system_data.get('security', {})
        }
        
        return render(request, 'modules/system_information/index.html', context)
        
    except Exception as e:
        logger.error(f"Sistem bilgileri görüntülenirken hata: {str(e)}")
        return render(request, 'modules/system_information/index.html', {
            'error': 'System information could not be loaded.'
        })


@login_required
def get_system_metrics_api(request):
    """
    Sistem metriklerini JSON olarak döndür (AJAX için)
    Uses cache for better performance
    """
    try:
        # Try to get from cache first
        system_data = SystemInfoCache.get_all_metrics()
        
        # If not in cache, collect fresh data and cache it
        if system_data is None:
            logger.info("Cache miss, collecting fresh system data")
            system_data = system_info_collector.get_all_system_info()
            SystemInfoCache.set_all_metrics(system_data)
        
        return JsonResponse({
            'success': True,
            'data': system_data,
            'cached': system_data is not None
        })
    except Exception as e:
        logger.error(f"Sistem metrikleri alınırken hata: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def get_cpu_info_api(request):
    """CPU bilgilerini JSON olarak döndür"""
    try:
        cpu_info = system_info_collector.get_cpu_info()
        return JsonResponse({
            'success': True,
            'data': cpu_info
        })
    except Exception as e:
        logger.error(f"CPU bilgileri alınırken hata: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def get_memory_info_api(request):
    """Bellek bilgilerini JSON olarak döndür"""
    try:
        memory_info = system_info_collector.get_memory_info()
        return JsonResponse({
            'success': True,
            'data': memory_info
        })
    except Exception as e:
        logger.error(f"Bellek bilgileri alınırken hata: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def get_disk_info_api(request):
    """Disk bilgilerini JSON olarak döndür"""
    try:
        disk_info = system_info_collector.get_disk_info()
        return JsonResponse({
            'success': True,
            'data': disk_info
        })
    except Exception as e:
        logger.error(f"Disk bilgileri alınırken hata: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def get_network_info_api(request):
    """Ağ bilgilerini JSON olarak döndür"""
    try:
        network_info = system_info_collector.get_network_info()
        return JsonResponse({
            'success': True,
            'data': network_info
        })
    except Exception as e:
        logger.error(f"Ağ bilgileri alınırken hata: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ===== SETTINGS API ENDPOINTS =====

@login_required
@require_http_methods(['GET'])
def get_service_status_api(request):
    """
    Get System Information service status and settings
    """
    try:
        if not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'Only administrators can view service status'
            }, status=403)
        
        settings = SystemInformationSettings.get_global_settings()
        cached_data = SystemInfoCache.get_all_metrics()
        
        return JsonResponse({
            'success': True,
            'settings': {
                'live_mode_enabled': settings.live_mode_enabled,
                'monitoring_interval': settings.monitoring_interval,
                'cache_duration': settings.cache_duration,
                'realtime_websocket_enabled': settings.realtime_websocket_enabled,
                'last_modified_by': settings.last_modified_by or 'Never',
                'updated_at': settings.updated_at.strftime('%Y-%m-%d %H:%M:%S') if settings.updated_at else 'Never'
            },
            'cache_available': cached_data is not None,
            'cache_info': {
                'has_cached_data': cached_data is not None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting service status: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(['POST'])
def toggle_live_mode_api(request):
    """
    Toggle live mode (admin only)
    """
    try:
        if not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'Only administrators can toggle live mode'
            }, status=403)
        
        data = json.loads(request.body)
        enabled = data.get('enabled', False)
        
        settings = SystemInformationSettings.get_global_settings()
        settings.live_mode_enabled = enabled
        settings.last_modified_by = request.user.username
        settings.save()
        
        # Update cache settings
        cache.set('system_info:live_mode', enabled, timeout=None)
        
        # Trigger immediate update if enabling
        if enabled:
            # Update cache immediately (synchronous)
            result = update_system_metrics()
            if result.get('success'):
                logger.info("System metrics updated successfully after enabling live mode")
            else:
                logger.error(f"Failed to update system metrics: {result.get('error')}")
            
            # Also schedule periodic updates via Celery
            update_system_metrics.delay()
        
        logger.info(f"Live mode {'enabled' if enabled else 'disabled'} by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': f"Live mode {'enabled' if enabled else 'disabled'}",
            'live_mode_enabled': enabled
        })
        
    except Exception as e:
        logger.error(f"Error toggling live mode: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(['POST'])
def update_monitoring_settings_api(request):
    """
    Update monitoring settings (admin only)
    """
    try:
        if not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'Only administrators can update settings'
            }, status=403)
        
        data = json.loads(request.body)
        
        monitoring_interval = float(data.get('monitoring_interval', 5.0))
        cache_duration = int(data.get('cache_duration', 10))
        
        # Validate ranges
        if not (1.0 <= monitoring_interval <= 60.0):
            return JsonResponse({
                'success': False,
                'error': 'Monitoring interval must be between 1.0 and 60.0 seconds'
            }, status=400)
        
        if not (5 <= cache_duration <= 600):
            return JsonResponse({
                'success': False,
                'error': 'Cache duration must be between 5 and 600 seconds'
            }, status=400)
        
        # Update settings
        settings = SystemInformationSettings.get_global_settings()
        settings.monitoring_interval = monitoring_interval
        settings.cache_duration = cache_duration
        settings.last_modified_by = request.user.username
        settings.save()
        
        # Update cache
        set_monitoring_interval(monitoring_interval)
        set_cache_duration(cache_duration)
        
        logger.info(f"Settings updated by {request.user.username}: interval={monitoring_interval}s, cache={cache_duration}s")
        
        return JsonResponse({
            'success': True,
            'message': 'Settings updated successfully',
            'settings': {
                'monitoring_interval': monitoring_interval,
                'cache_duration': cache_duration
            }
        })
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': 'Invalid number format'
        }, status=400)
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(['POST'])
def force_cache_update_api(request):
    """
    Force an immediate cache update
    """
    try:
        if not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'Only administrators can force updates'
            }, status=403)
        
        # Clear existing cache
        SystemInfoCache.clear_all()
        
        # Trigger immediate update
        result = update_system_metrics.delay()
        
        logger.info(f"Cache update forced by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Cache update triggered successfully'
        })
        
    except Exception as e:
        logger.error(f"Error forcing cache update: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(['GET'])
def get_live_mode_status_api(request):
    """
    Get live mode status and cache availability
    """
    try:
        settings = SystemInformationSettings.get_global_settings()
        cached_data = SystemInfoCache.get_all_metrics()
        
        return JsonResponse({
            'success': True,
            'live_mode_enabled': settings.live_mode_enabled,
            'cache_available': cached_data is not None,
            'monitoring_interval': settings.monitoring_interval,
            'cache_duration': settings.cache_duration,
            'realtime_websocket_enabled': settings.realtime_websocket_enabled
        })
        
    except Exception as e:
        logger.error(f"Error getting live mode status: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ===== LOGGING API ENDPOINTS =====

@require_http_methods(["GET"])
@login_required
def get_logging_status(request):
    """Get System Information logging status"""
    try:
        settings = SystemInformationSettings.get_global_settings()
        return JsonResponse({
            'success': True,
            'logging_enabled': settings.logging_enabled,
            'log_retention_days': settings.log_retention_days,
            'last_modified_by': settings.last_modified_by or 'N/A'
        })
    except Exception as e:
        logger.error(f"Error getting System Information logging status: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["POST"])
@login_required
def toggle_logging(request):
    """Toggle System Information logging"""
    try:
        data = json.loads(request.body)
        settings = SystemInformationSettings.get_global_settings()
        
        # Update logging settings
        if 'logging_enabled' in data:
            settings.logging_enabled = bool(data['logging_enabled'])
        
        if 'log_retention_days' in data:
            settings.log_retention_days = int(data['log_retention_days'])
        
        settings.last_modified_by = request.user.username
        settings.save()
        
        # Log the logging toggle operation
        log_system_operation(
            operation_type='system_info',
            status='success',
            message=f"Logging {'enabled' if settings.logging_enabled else 'disabled'} by {request.user.username}",
            user=request.user.username,
            ip_address=request.META.get('REMOTE_ADDR'),
            details={'logging_enabled': settings.logging_enabled}
        )
        
        return JsonResponse({
            'success': True,
            'message': f"Logging {'enabled' if settings.logging_enabled else 'disabled'} successfully",
            'logging_enabled': settings.logging_enabled,
            'log_retention_days': settings.log_retention_days
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error toggling System Information logging: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
