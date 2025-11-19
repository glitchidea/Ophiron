"""
Docker Hub API Manager
Docker Hub'dan veri çeken modüler sistem
"""

import requests
import json
import time
import gzip
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class DockerHubAPI:
    """Docker Hub API yöneticisi"""
    
    def __init__(self):
        self.base_url = "https://hub.docker.com/v2"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Ophiron-Docker-Manager/1.0',
            'Accept': 'application/json'
        })
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """API isteği yap"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API isteği hatası: {e}")
            return None
    
    def get_categories(self) -> Dict:
        """Kategorileri al - Her seferinde fresh data"""
        # API'den veri çek
        categories = {
            'products': [
                {'name': 'Images', 'value': 'images', 'icon': 'fas fa-images'},
                {'name': 'Extensions', 'value': 'extensions', 'icon': 'fas fa-puzzle-piece'},
                {'name': 'Plugins', 'value': 'plugins', 'icon': 'fas fa-plug'},
                {'name': 'Compose', 'value': 'compose', 'icon': 'fas fa-layer-group'},
                {'name': 'AI Models', 'value': 'ai-models', 'icon': 'fas fa-robot'},
            ],
            'trusted_content': [
                {'name': 'Docker Official Image', 'value': 'official', 'icon': 'fas fa-shield-alt'},
                {'name': 'Verified Publisher', 'value': 'verified', 'icon': 'fas fa-check-circle'},
                {'name': 'Sponsored OSS', 'value': 'sponsored', 'icon': 'fas fa-star'},
            ],
            'categories': [
                {'name': 'Networking', 'value': 'networking', 'icon': 'fas fa-network-wired'},
                {'name': 'Security', 'value': 'security', 'icon': 'fas fa-shield-alt'},
                {'name': 'Languages & frameworks', 'value': 'languages', 'icon': 'fas fa-code'},
                {'name': 'Integration & delivery', 'value': 'integration', 'icon': 'fas fa-shipping-fast'},
                {'name': 'Message queues', 'value': 'message-queues', 'icon': 'fas fa-exchange-alt'},
            ],
            'operating_systems': [
                {'name': 'Linux', 'value': 'linux', 'icon': 'fab fa-linux'},
                {'name': 'Windows', 'value': 'windows', 'icon': 'fab fa-windows'},
            ],
            'architectures': [
                {'name': 'x86-64', 'value': 'amd64', 'icon': 'fas fa-microchip'},
                {'name': 'ARM 64', 'value': 'arm64', 'icon': 'fas fa-microchip'},
                {'name': 'ARM', 'value': 'arm', 'icon': 'fas fa-microchip'},
                {'name': 'IBM Z', 'value': 's390x', 'icon': 'fas fa-microchip'},
                {'name': 'x86', 'value': '386', 'icon': 'fas fa-microchip'},
            ]
        }
        
        return categories
    
    def search_repositories(self, query: str = "", page: int = 1, page_size: int = 25, 
                          category: str = None, os: str = None, arch: str = None) -> Dict:
        """Repository arama"""
        # Eğer tüm imajları istiyorsa sayfalama yap - Sınırsız
        if page_size >= 25 and not query:
            data = self.get_all_official_images()
            if data:
                # Tüm veriyi döndür (sayfalama yapma)
                return {
                    'count': data['count'],
                    'results': data['results'],
                    'next': None,
                    'previous': None
                }
        
        # API parametreleri
        params = {
            'page': page,
            'page_size': page_size
        }
        
        if query:
            params['q'] = query
        
        # API isteği - Library namespace'inden resmi imajları al
        data = self._make_request('/repositories/library/', params)
        if not data:
            return {'count': 0, 'results': [], 'next': None, 'previous': None}
        
        return data
    
    def get_all_official_images(self, force_refresh: bool = False) -> Dict:
        """Tüm resmi imajları sayfalama ile al - Her seferinde fresh data"""
        all_images = []
        page = 1
        total_count = 0
        
        while True:
            params = {
                'page': page,
                'page_size': 100  # Docker Hub API maksimum limiti
            }
            
            data = self._make_request('/repositories/library/', params)
            if not data or not data.get('results'):
                break
            
            all_images.extend(data['results'])
            total_count = data.get('count', 0)
            
            # Son sayfa kontrolü
            if not data.get('next'):
                break
                
            page += 1
        
        result = {
            'count': len(all_images),
            'results': all_images,
            'next': None,
            'previous': None,
            'total_available': total_count
        }
        
        return result
    
    def get_official_images(self, page: int = 1, page_size: int = 25) -> Dict:
        """Resmi Docker imajlarını al - Her seferinde fresh data"""
        # Library namespace'inden resmi imajları al
        params = {
            'page': page,
            'page_size': page_size
        }
        
        data = self._make_request('/repositories/library/', params)
        if not data:
            return {'count': 0, 'results': [], 'next': None, 'previous': None}
        
        return data
    
    def get_repository_details(self, namespace: str, name: str) -> Optional[Dict]:
        """Repository detaylarını al - Her seferinde fresh data"""
        # API isteği
        data = self._make_request(f'/repositories/{namespace}/{name}/')
        if not data:
            return None
        
        return data
    
    def get_repository_tags(self, namespace: str, name: str, page: int = 1) -> Dict:
        """Repository tag'lerini al - Her seferinde fresh data"""
        # API parametreleri
        params = {
            'page': page,
            'page_size': 25,
            'ordering': '-last_updated'
        }
        
        # API isteği
        data = self._make_request(f'/repositories/{namespace}/{name}/tags/', params)
        if not data:
            return {'count': 0, 'results': [], 'next': None, 'previous': None}
        
        return data
    
    def get_popular_images(self, limit: int = 100, force_refresh: bool = False) -> List[Dict]:
        """Popüler imajları al - Her seferinde fresh data, sınırsız"""
        # Resmi imajları al (sayfalama ile) - Sınırsız
        if limit >= 25:  # Tüm imajları istiyorsa
            data = self.get_all_official_images()
            if not data or 'results' not in data:
                return []
            repos = data['results']
        else:  # Sınırlı sayıda imaj istiyorsa
            data = self.get_official_images(page=1, page_size=limit)
            if not data or 'results' not in data:
                return []
            repos = data['results']
        
        # Veriyi formatla
        images = []
        for repo in repos:
            image = {
                'name': repo['name'],
                'namespace': repo['namespace'],
                'description': repo.get('description', ''),
                'stars': repo.get('star_count', 0),
                'pulls': repo.get('pull_count', 0),
                'official': repo['namespace'] == 'library',
                'last_updated': repo.get('last_updated', ''),
                'categories': [cat['name'] for cat in repo.get('categories', [])],
                'tags': []  # Tag'ler ayrıca çekilecek
            }
            images.append(image)
        
        return images
    
    def refresh_all_data(self, progress_callback=None) -> Dict:
        """Tüm verileri yenile"""
        try:
            total_steps = 4
            current_step = 0
            results = {
                'success': True,
                'images_loaded': 0,
                'categories_loaded': 0,
                'total_time': 0,
                'steps_completed': 0,
                'progress_percentage': 0
            }
            
            start_time = time.time()
            
            # Step 1: Kategorileri yenile
            if progress_callback:
                progress_callback(current_step, total_steps, "Loading categories...")
            
            categories = self.get_categories()
            results['categories_loaded'] = len(categories.get('products', [])) + len(categories.get('categories', []))
            current_step += 1
            
            # Step 2: Popüler imajları yenile
            if progress_callback:
                progress_callback(current_step, total_steps, "Loading popular images...")
            
            images = self.get_popular_images(limit=10000)  # Sınırsız
            results['images_loaded'] = len(images)
            current_step += 1
            
            # Step 3: Tamamlandı
            if progress_callback:
                progress_callback(current_step, total_steps, "Refresh completed!")
            
            end_time = time.time()
            results['total_time'] = round(end_time - start_time, 2)
            results['steps_completed'] = current_step
            results['progress_percentage'] = 100
            
            return results
            
        except Exception as e:
            logger.error(f"Refresh all data error: {e}")
            return {
                'success': False,
                'error': str(e),
                'progress_percentage': 0
            }
    

