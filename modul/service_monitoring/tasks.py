"""
Service Monitoring Celery Tasks
Background tasks for service monitoring operations
"""

import logging
from celery import shared_task
from django.core.cache import cache
from .service_manager import ServiceManager

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def update_cache(self):
    """
    Update Service Monitoring cache
    This task runs periodically to keep service data fresh
    """
    try:
        service_manager = ServiceManager()
        
        # Get current services data
        services = service_manager.get_services()
        
        # Cache the data with a reasonable timeout
        cache.set('service_monitoring_services', services, timeout=300)  # 5 minutes
        
        # Update cache timestamp
        from datetime import datetime
        cache.set('service_monitoring_last_update', datetime.now().isoformat(), timeout=300)
        
        logger.info(f"Service Monitoring cache updated: {len(services)} services")
        
        return {
            'success': True,
            'services_count': len(services),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating Service Monitoring cache: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def cleanup_expired_cache(self):
    """
    Clean up expired Service Monitoring cache entries
    This task runs periodically to remove old cache data
    """
    try:
        # Get cache keys related to service monitoring
        cache_keys = [
            'service_monitoring_services',
            'service_monitoring_last_update',
            'service_monitoring_stats'
        ]
        
        cleaned_count = 0
        for key in cache_keys:
            if cache.get(key) is not None:
                cache.delete(key)
                cleaned_count += 1
        
        logger.info(f"Service Monitoring cache cleanup completed: {cleaned_count} entries removed")
        
        return {
            'success': True,
            'cleaned_entries': cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning Service Monitoring cache: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def force_refresh_services(self):
    """
    Force refresh of all service data
    This task can be called manually to update service information
    """
    try:
        service_manager = ServiceManager()
        
        # Force refresh services (bypass cache)
        services = service_manager.get_services(force_refresh=True)
        
        # Update cache with fresh data
        cache.set('service_monitoring_services', services, timeout=300)
        
        # Update cache timestamp
        from datetime import datetime
        cache.set('service_monitoring_last_update', datetime.now().isoformat(), timeout=300)
        
        logger.info(f"Service Monitoring force refresh completed: {len(services)} services")
        
        return {
            'success': True,
            'services_count': len(services),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error force refreshing Service Monitoring: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def monitor_service_health(self, service_name):
    """
    Monitor specific service health
    This task can be used to monitor critical services
    """
    try:
        service_manager = ServiceManager()
        
        # Get service details
        service_details = service_manager.get_service_details(service_name)
        
        # Check if service is healthy
        is_healthy = service_details.get('status') == 'active'
        
        # Log health status
        if is_healthy:
            logger.info(f"Service {service_name} is healthy")
        else:
            logger.warning(f"Service {service_name} is not healthy: {service_details.get('status')}")
        
        return {
            'success': True,
            'service_name': service_name,
            'is_healthy': is_healthy,
            'status': service_details.get('status'),
            'details': service_details
        }
        
    except Exception as e:
        logger.error(f"Error monitoring service {service_name}: {str(e)}")
        return {
            'success': False,
            'service_name': service_name,
            'error': str(e)
        }
