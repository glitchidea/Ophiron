"""
System Information Celery Tasks
Background tasks for collecting and caching system information
"""

import logging
from celery import shared_task
from celery.schedules import schedule
from django.core.cache import cache
from django.conf import settings

from .utils import SystemInfo
from .cache import SystemInfoCache

logger = logging.getLogger(__name__)


# Singleton instance of SystemInfo
system_info_collector = None


def get_system_info_collector():
    """Get or create SystemInfo collector instance"""
    global system_info_collector
    if system_info_collector is None:
        system_info_collector = SystemInfo()
    return system_info_collector


@shared_task(name='system_information.update_system_metrics')
def update_system_metrics():
    """
    Celery task to update system metrics in cache.
    This task runs periodically based on the monitoring interval.
    """
    try:
        logger.info("Starting system metrics update task...")
        
        # Get monitoring settings
        monitoring_interval = cache.get('system_info:monitoring_interval', 5)
        cache_duration = cache.get('system_info:cache_duration', 10)
        
        # Collect system information
        collector = get_system_info_collector()
        
        # Get all metrics
        metrics = {
            'cpu': collector.get_cpu_info(),
            'memory': collector.get_memory_info(),
            'disk': collector.get_disk_info(),
            'network': collector.get_network_info(),
            'os_info': collector.get_os_info(),
            'users': collector.get_system_users(),
            'security': collector.get_security_info(),
        }
        
        # Cache the data
        SystemInfoCache.set_all_metrics(metrics, timeout=cache_duration)
        
        logger.info(f"System metrics updated successfully (interval: {monitoring_interval}s, cache: {cache_duration}s)")
        
        return {
            'success': True,
            'message': 'System metrics updated',
            'metrics_count': len(metrics)
        }
        
    except Exception as e:
        logger.error(f"Error in update_system_metrics task: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(name='system_information.update_cpu_metrics')
def update_cpu_metrics():
    """Update only CPU metrics (lightweight)"""
    try:
        collector = get_system_info_collector()
        cpu_info = collector.get_cpu_info()
        
        cache_duration = cache.get('system_info:cache_duration', 10)
        SystemInfoCache.set_cache('cpu', cpu_info, timeout=cache_duration)
        
        logger.debug("CPU metrics updated")
        return {'success': True}
    except Exception as e:
        logger.error(f"Error updating CPU metrics: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task(name='system_information.update_memory_metrics')
def update_memory_metrics():
    """Update only memory metrics (lightweight)"""
    try:
        collector = get_system_info_collector()
        memory_info = collector.get_memory_info()
        
        cache_duration = cache.get('system_info:cache_duration', 10)
        SystemInfoCache.set_cache('memory', memory_info, timeout=cache_duration)
        
        logger.debug("Memory metrics updated")
        return {'success': True}
    except Exception as e:
        logger.error(f"Error updating memory metrics: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task(name='system_information.update_disk_metrics')
def update_disk_metrics():
    """Update only disk metrics (heavier, less frequent)"""
    try:
        collector = get_system_info_collector()
        disk_info = collector.get_disk_info()
        
        cache_duration = cache.get('system_info:cache_duration', 10)
        SystemInfoCache.set_cache('disk', disk_info, timeout=cache_duration)
        
        logger.debug("Disk metrics updated")
        return {'success': True}
    except Exception as e:
        logger.error(f"Error updating disk metrics: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task(name='system_information.update_network_metrics')
def update_network_metrics():
    """Update only network metrics"""
    try:
        collector = get_system_info_collector()
        network_info = collector.get_network_info()
        
        cache_duration = cache.get('system_info:cache_duration', 10)
        SystemInfoCache.set_cache('network', network_info, timeout=cache_duration)
        
        logger.debug("Network metrics updated")
        return {'success': True}
    except Exception as e:
        logger.error(f"Error updating network metrics: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task(name='system_information.clear_cache')
def clear_system_info_cache():
    """Clear all system information caches"""
    try:
        SystemInfoCache.clear_all()
        logger.info("System information cache cleared")
        return {'success': True}
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return {'success': False, 'error': str(e)}


def get_monitoring_interval():
    """Get the current monitoring interval from cache or default"""
    return cache.get('system_info:monitoring_interval', 5)


def set_monitoring_interval(interval):
    """Set the monitoring interval (seconds)"""
    try:
        interval = int(interval)
        if interval < 1:
            interval = 1
        elif interval > 300:  # Max 5 minutes
            interval = 300
        
        cache.set('system_info:monitoring_interval', interval, timeout=None)
        logger.info(f"Monitoring interval set to {interval}s")
        return True
    except Exception as e:
        logger.error(f"Error setting monitoring interval: {str(e)}")
        return False


def get_cache_duration():
    """Get the current cache duration from cache or default"""
    return cache.get('system_info:cache_duration', 10)


def set_cache_duration(duration):
    """Set the cache duration (seconds)"""
    try:
        duration = int(duration)
        if duration < 5:
            duration = 5
        elif duration > 600:  # Max 10 minutes
            duration = 600
        
        cache.set('system_info:cache_duration', duration, timeout=None)
        logger.info(f"Cache duration set to {duration}s")
        return True
    except Exception as e:
        logger.error(f"Error setting cache duration: {str(e)}")
        return False

