"""
Docker Hub Cache Views
Handles cached data operations
"""

import logging
from django.http import JsonResponse
from .docker_hub_cache import docker_hub_cache

logger = logging.getLogger(__name__)

def search_cached_images(request):
    """Search images in cached data"""
    try:
        query = request.GET.get('q', '').strip()
        
        # Get cached images
        images = docker_hub_cache.get_cached_images()
        
        if not images:
            return JsonResponse({
                'success': False,
                'message': 'No cached data available. Please refresh first.',
                'results': []
            })
        
        # Search in cached data
        if query:
            results = docker_hub_cache.search_images(query)
        else:
            results = images
        
        return JsonResponse({
            'success': True,
            'results': results,
            'count': len(results),
            'total_cached': len(images),
            'query': query
        })
        
    except Exception as e:
        logger.error(f"Error in search_cached_images: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Search error: {str(e)}'
        })

def get_cached_images(request):
    """Get all cached images"""
    try:
        images = docker_hub_cache.get_cached_images()
        
        return JsonResponse({
            'success': True,
            'results': images,
            'count': len(images)
        })
        
    except Exception as e:
        logger.error(f"Error in get_cached_images: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })

def get_cache_info(request):
    """Get cache information"""
    try:
        info = docker_hub_cache.get_cache_info()
        
        return JsonResponse({
            'success': True,
            'cache_info': info
        })
        
    except Exception as e:
        logger.error(f"Error in get_cache_info: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })

def clear_cache(request):
    """Clear cache"""
    try:
        success = docker_hub_cache.clear_cache()
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Cache cleared successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to clear cache'
            })
        
    except Exception as e:
        logger.error(f"Error in clear_cache: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })





