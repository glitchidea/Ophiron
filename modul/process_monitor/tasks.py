"""
Celery Tasks for Process Monitor
Arka planda çalışan monitoring task'ları
"""

import logging
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from .utils import process_monitor
from .models import ProcessMonitorSettings, ProcessMonitorCache

logger = logging.getLogger(__name__)


@shared_task(name='process_monitor.update_cache')
def update_process_monitor_cache():
    """
    Process Monitor verilerini cache'e yükle ve WebSocket ile broadcast et
    Bu task arka planda sürekli çalışır (Celery Beat ile, dinamik interval)
    """
    try:
        # Global ayarları kontrol et
        settings = ProcessMonitorSettings.get_global_settings()
        
        if not settings.live_mode_enabled or not settings.background_service_enabled:
            # Live mode kapalıysa çalışma
            return {
                'status': 'skipped',
                'message': 'Live mode disabled',
                'timestamp': timezone.now().isoformat()
            }
        
        logger.debug(f"🔄 Cache güncelleniyor... (Interval: {settings.monitoring_interval}s)")
        
        # Connections verilerini al
        connections = process_monitor.get_network_connections()
        
        # Ports verilerini al
        ports = process_monitor.get_most_used_ports(limit=6)
        
        # Redis cache'e yaz
        cache.set('process_monitor:connections', connections, timeout=settings.cache_duration)
        cache.set('process_monitor:ports', ports, timeout=settings.cache_duration)
        
        # Database cache'e de yaz (fallback için)
        ProcessMonitorCache.set_cache('connections', connections, duration=settings.cache_duration)
        ProcessMonitorCache.set_cache('ports', ports, duration=settings.cache_duration)
        
        # WebSocket broadcast (eğer enabled ise)
        if settings.realtime_websocket_enabled:
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                
                channel_layer = get_channel_layer()
                if channel_layer:
                    # Connections broadcast
                    async_to_sync(channel_layer.group_send)(
                        'process_monitor_updates',
                        {
                            'type': 'send_connections_update',
                            'connections': connections
                        }
                    )
                    # Ports broadcast
                    async_to_sync(channel_layer.group_send)(
                        'process_monitor_updates',
                        {
                            'type': 'send_ports_update',
                            'ports': ports
                        }
                    )
                    logger.debug(f"✓ WebSocket broadcast: {len(connections)} bağlantı, {len(ports)} port")
            except Exception as ws_error:
                logger.warning(f"WebSocket broadcast hatası: {str(ws_error)}")
        
        logger.info(f"✓ Cache güncellendi: {len(connections)} bağlantı, {len(ports)} port")
        
        return {
            'status': 'success',
            'connections_count': len(connections),
            'ports_count': len(ports),
            'interval': settings.monitoring_interval,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Cache güncelleme hatası: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task(name='process_monitor.cleanup_expired_cache')
def cleanup_expired_cache():
    """
    Süresi dolmuş cache kayıtlarını temizle
    Her 30 dakikada bir çalışır (celery beat)
    """
    try:
        from .models import ProcessMonitorCache
        ProcessMonitorCache.clear_expired()
        logger.info("Süresi dolmuş cache kayıtları temizlendi")
        return {'status': 'success', 'timestamp': timezone.now().isoformat()}
    except Exception as e:
        logger.error(f"Cache temizleme hatası: {str(e)}")
        return {'status': 'error', 'error': str(e)}


@shared_task(name='process_monitor.start_monitoring')
def start_monitoring_for_user(user_id):
    """
    Kullanıcı için monitoring başlat
    """
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id)
        settings = ProcessMonitorSettings.get_or_create_for_user(user)
        
        if not settings.live_mode_enabled:
            return {'status': 'disabled', 'message': 'Live mode kapalı'}
        
        # Periyodik task başlat
        interval = settings.monitoring_interval
        from celery import current_app
        
        # Task ID oluştur
        task_id = f'process_monitor_user_{user_id}'
        
        # Periyodik task schedule et
        current_app.send_task(
            'process_monitor.update_cache',
            task_id=task_id
        )
        
        logger.info(f"Monitoring başlatıldı: User {user_id}, Interval: {interval}s")
        
        return {
            'status': 'started',
            'user_id': user_id,
            'interval': interval,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Monitoring başlatma hatası: {str(e)}")
        return {'status': 'error', 'error': str(e)}


@shared_task(name='process_monitor.stop_monitoring')
def stop_monitoring_for_user(user_id):
    """
    Kullanıcı için monitoring durdur
    """
    try:
        from celery import current_app
        
        # Task ID
        task_id = f'process_monitor_user_{user_id}'
        
        # Task'ı iptal et
        current_app.control.revoke(task_id, terminate=True)
        
        logger.info(f"Monitoring durduruldu: User {user_id}")
        
        return {
            'status': 'stopped',
            'user_id': user_id,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Monitoring durdurma hatası: {str(e)}")
        return {'status': 'error', 'error': str(e)}


@shared_task(name='process_monitor.continuous_monitoring')
def continuous_monitoring():
    """
    Tüm aktif kullanıcılar için sürekli monitoring
    Bu task celery beat ile her saniye çalışır
    """
    try:
        # Live mode açık olan kullanıcıları bul
        active_settings = ProcessMonitorSettings.objects.filter(
            live_mode_enabled=True,
            background_service_enabled=True
        )
        
        if not active_settings.exists():
            return {'status': 'no_active_users', 'timestamp': timezone.now().isoformat()}
        
        # Cache güncelle
        update_process_monitor_cache.delay()
        
        logger.info(f"Continuous monitoring: {active_settings.count()} aktif kullanıcı")
        
        return {
            'status': 'success',
            'active_users': active_settings.count(),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Continuous monitoring hatası: {str(e)}")
        return {'status': 'error', 'error': str(e)}

