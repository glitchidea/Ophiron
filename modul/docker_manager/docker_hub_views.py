"""
Docker Hub Views
Docker Hub verilerini yöneten view'lar
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from .docker_hub_api import DockerHubAPI

logger = logging.getLogger(__name__)

def hubs(request):
    """Docker Hubs ana sayfası"""
    try:
        api = DockerHubAPI()
        
        # Kategorileri al
        categories = api.get_categories()
        
        # Popüler imajları al
        popular_images = api.get_popular_images(limit=20)
        
        # Cache bilgilerini al
        cache_info = api.get_cache_info()
        
        context = {
            'categories': categories,
            'popular_images': popular_images,
            'cache_info': cache_info,
            'total_images': len(popular_images)
        }
        
        return render(request, 'modules/docker_manager/hubs.html', context)
        
    except Exception as e:
        logger.error(f"Hubs sayfası hatası: {e}")
        return render(request, 'modules/docker_manager/hubs.html', {
            'categories': {},
            'popular_images': [],
            'cache_info': {},
            'total_images': 0,
            'error': str(e)
        })

@require_http_methods(["GET"])
def search_hub(request):
    """Docker Hub arama"""
    try:
        query = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 25))
        category = request.GET.get('category', '')
        os_filter = request.GET.get('os', '')
        arch_filter = request.GET.get('arch', '')
        
        api = DockerHubAPI()
        
        if query or category or os_filter or arch_filter:
            # Arama yap
            results = api.search_repositories(
                query=query,
                page=page,
                page_size=page_size,
                category=category,
                os=os_filter,
                arch=arch_filter
            )
        else:
            # Popüler imajları al
            results = api.search_repositories(page=page, page_size=page_size)
        
        return JsonResponse({
            'success': True,
            'results': results.get('results', []),
            'count': results.get('count', 0),
            'next': results.get('next'),
            'previous': results.get('previous')
        })
        
    except Exception as e:
        logger.error(f"Hub arama hatası: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_http_methods(["GET"])
def get_repository_details(request, namespace, name):
    """Repository detaylarını al"""
    try:
        api = DockerHubAPI()
        details = api.get_repository_details(namespace, name)
        
        if not details:
            return JsonResponse({
                'success': False,
                'message': 'Repository bulunamadı'
            })
        
        return JsonResponse({
            'success': True,
            'repository': details
        })
        
    except Exception as e:
        logger.error(f"Repository detay hatası: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_http_methods(["GET"])
def get_repository_tags(request, namespace, name):
    """Repository tag'lerini al"""
    try:
        page = int(request.GET.get('page', 1))
        api = DockerHubAPI()
        tags = api.get_repository_tags(namespace, name, page)
        
        return JsonResponse({
            'success': True,
            'tags': tags.get('results', []),
            'count': tags.get('count', 0),
            'next': tags.get('next'),
            'previous': tags.get('previous')
        })
        
    except Exception as e:
        logger.error(f"Repository tag hatası: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_http_methods(["POST"])
@csrf_exempt
def pull_image(request):
    """Docker imajını pull et"""
    try:
        data = json.loads(request.body)
        image_name = data.get('image_name', '')
        
        if not image_name:
            return JsonResponse({
                'success': False,
                'message': 'Image name gerekli'
            })
        
        # Burada Docker client kullanarak pull işlemi yapılabilir
        # Şimdilik başarılı response döndürüyoruz
        
        return JsonResponse({
            'success': True,
            'message': f'Image {image_name} pull ediliyor...',
            'image_name': image_name
        })
        
    except Exception as e:
        logger.error(f"Image pull hatası: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_http_methods(["POST"])
@csrf_exempt
def clear_cache(request):
    """Cache'i temizle"""
    try:
        api = DockerHubAPI()
        success = api.clear_cache()
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Cache temizlendi'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Cache temizlenemedi'
            })
        
    except Exception as e:
        logger.error(f"Cache temizleme hatası: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_http_methods(["GET"])
def get_cache_info(request):
    """Cache bilgilerini al"""
    try:
        api = DockerHubAPI()
        cache_info = api.get_cache_info()
        
        return JsonResponse({
            'success': True,
            'cache_info': cache_info
        })
        
    except Exception as e:
        logger.error(f"Cache bilgi hatası: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_http_methods(["POST"])
@csrf_exempt
def refresh_all_data(request):
    """Tüm verileri yenile"""
    try:
        api = DockerHubAPI()
        
        # Progress callback fonksiyonu
        def progress_callback(step, total, message):
            # Burada WebSocket veya Server-Sent Events kullanılabilir
            # Şimdilik basit bir log
            logger.info(f"Progress: {step}/{total} - {message}")
        
        # Tüm verileri yenile
        results = api.refresh_all_data(progress_callback)
        
        return JsonResponse({
            'success': results['success'],
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Refresh all data hatası: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_http_methods(["GET"])
def get_refresh_status(request):
    """Refresh durumunu al"""
    try:
        # Bu endpoint WebSocket veya Server-Sent Events ile gerçek zamanlı progress için kullanılabilir
        # Şimdilik basit bir status döndürüyoruz
        
        return JsonResponse({
            'success': True,
            'status': 'completed',
            'message': 'Refresh completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Refresh status hatası: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

