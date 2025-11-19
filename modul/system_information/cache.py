"""
System Information Cache Management
Manages caching of system information data for performance optimization
"""

import logging
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class SystemInfoCache:
    """
    Manages caching for system information data.
    Similar to ProcessMonitorCache but for system metrics.
    """
    
    # Cache key prefixes
    CACHE_PREFIX = 'system_info'
    
    # Cache keys
    CPU_KEY = f'{CACHE_PREFIX}:cpu'
    MEMORY_KEY = f'{CACHE_PREFIX}:memory'
    DISK_KEY = f'{CACHE_PREFIX}:disk'
    NETWORK_KEY = f'{CACHE_PREFIX}:network'
    OS_KEY = f'{CACHE_PREFIX}:os'
    USERS_KEY = f'{CACHE_PREFIX}:users'
    SECURITY_KEY = f'{CACHE_PREFIX}:security'
    ALL_KEY = f'{CACHE_PREFIX}:all'
    
    # Default cache timeout (in seconds)
    DEFAULT_TIMEOUT = getattr(settings, 'SYSTEM_INFO_CACHE_TIMEOUT', 5)
    
    @classmethod
    def set_cache(cls, key, data, timeout=None):
        """
        Set cache data with optional timeout
        
        Args:
            key: Cache key (without prefix)
            data: Data to cache
            timeout: Cache timeout in seconds (None = default)
        """
        try:
            cache_key = f'{cls.CACHE_PREFIX}:{key}'
            if timeout is None:
                timeout = cls.DEFAULT_TIMEOUT
            cache.set(cache_key, data, timeout)
            logger.debug(f"Cache set: {cache_key} (timeout: {timeout}s)")
            return True
        except Exception as e:
            logger.error(f"Error setting cache {key}: {str(e)}")
            return False
    
    @classmethod
    def get_cache(cls, key):
        """
        Get cached data
        
        Args:
            key: Cache key (without prefix)
        
        Returns:
            Cached data or None if not found
        """
        try:
            cache_key = f'{cls.CACHE_PREFIX}:{key}'
            data = cache.get(cache_key)
            if data is not None:
                logger.debug(f"Cache hit: {cache_key}")
            else:
                logger.debug(f"Cache miss: {cache_key}")
            return data
        except Exception as e:
            logger.error(f"Error getting cache {key}: {str(e)}")
            return None
    
    @classmethod
    def delete_cache(cls, key):
        """
        Delete cached data
        
        Args:
            key: Cache key (without prefix)
        """
        try:
            cache_key = f'{cls.CACHE_PREFIX}:{key}'
            cache.delete(cache_key)
            logger.debug(f"Cache deleted: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting cache {key}: {str(e)}")
            return False
    
    @classmethod
    def clear_all(cls):
        """Clear all system information caches"""
        try:
            keys = ['cpu', 'memory', 'disk', 'network', 'os', 'users', 'security', 'all']
            for key in keys:
                cls.delete_cache(key)
            logger.info("All system information caches cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing all caches: {str(e)}")
            return False
    
    @classmethod
    def set_all_metrics(cls, metrics_data, timeout=None):
        """
        Set all metrics at once
        
        Args:
            metrics_data: Dictionary containing all system metrics
            timeout: Cache timeout in seconds
        """
        try:
            timeout = timeout or cls.DEFAULT_TIMEOUT
            
            # Cache individual metrics
            if 'cpu' in metrics_data:
                cls.set_cache('cpu', metrics_data['cpu'], timeout)
            
            if 'memory' in metrics_data:
                cls.set_cache('memory', metrics_data['memory'], timeout)
            
            if 'disk' in metrics_data:
                cls.set_cache('disk', metrics_data['disk'], timeout)
            
            if 'network' in metrics_data:
                cls.set_cache('network', metrics_data['network'], timeout)
            
            if 'os_info' in metrics_data:
                cls.set_cache('os', metrics_data['os_info'], timeout)
            
            if 'users' in metrics_data:
                cls.set_cache('users', metrics_data['users'], timeout)
            
            if 'security' in metrics_data:
                cls.set_cache('security', metrics_data['security'], timeout)
            
            # Cache the complete data
            cls.set_cache('all', metrics_data, timeout)
            
            logger.info("All system metrics cached successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error caching all metrics: {str(e)}")
            return False
    
    @classmethod
    def get_all_metrics(cls):
        """
        Get all cached metrics
        
        Returns:
            Dictionary containing all cached metrics or None
        """
        return cls.get_cache('all')

