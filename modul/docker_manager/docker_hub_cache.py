"""
Docker Hub Cache Manager
Handles caching of Docker Hub data locally
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

class DockerHubCache:
    """Docker Hub data cache manager"""
    
    def __init__(self):
        """Initialize cache manager"""
        self.cache_dir = os.path.join(settings.BASE_DIR, 'cache')
        self.images_file = os.path.join(self.cache_dir, 'docker_images.json')
        self.categories_file = os.path.join(self.cache_dir, 'docker_categories.json')
        self.cache_duration = 30 * 60  # 30 minutes in seconds
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _is_cache_valid(self, file_path: str) -> bool:
        """Check if cache file is valid and not expired"""
        if not os.path.exists(file_path):
            return False
        
        file_age = time.time() - os.path.getmtime(file_path)
        return file_age < self.cache_duration
    
    def _load_from_cache(self, file_path: str) -> Optional[Dict]:
        """Load data from cache file"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cache from {file_path}: {e}")
        return None
    
    def _save_to_cache(self, data: Dict, file_path: str) -> bool:
        """Save data to cache file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving cache to {file_path}: {e}")
            return False
    
    def get_cached_images(self) -> List[Dict]:
        """Get cached images data"""
        if self._is_cache_valid(self.images_file):
            data = self._load_from_cache(self.images_file)
            if data and 'images' in data:
                return data['images']
        return []
    
    def save_images(self, images: List[Dict]) -> bool:
        """Save images to cache"""
        cache_data = {
            'images': images,
            'cached_at': time.time(),
            'count': len(images)
        }
        return self._save_to_cache(cache_data, self.images_file)
    
    def get_cached_categories(self) -> Dict:
        """Get cached categories data"""
        if self._is_cache_valid(self.categories_file):
            data = self._load_from_cache(self.categories_file)
            if data and 'categories' in data:
                return data['categories']
        return {}
    
    def save_categories(self, categories: Dict) -> bool:
        """Save categories to cache"""
        cache_data = {
            'categories': categories,
            'cached_at': time.time()
        }
        return self._save_to_cache(cache_data, self.categories_file)
    
    def search_images(self, query: str) -> List[Dict]:
        """Search images in cached data"""
        images = self.get_cached_images()
        if not images:
            return []
        
        query = query.lower().strip()
        if not query:
            return images
        
        # Search in name, description, and tags
        results = []
        for image in images:
            name = image.get('name', '').lower()
            description = image.get('description', '').lower()
            tags = ' '.join(image.get('tags', [])).lower()
            
            if (query in name or 
                query in description or 
                query in tags):
                results.append(image)
        
        return results
    
    def get_cache_info(self) -> Dict:
        """Get cache information"""
        info = {
            'images_count': 0,
            'categories_count': 0,
            'images_age': 0,
            'categories_age': 0,
            'cache_valid': False
        }
        
        # Check images cache
        if os.path.exists(self.images_file):
            data = self._load_from_cache(self.images_file)
            if data:
                info['images_count'] = data.get('count', 0)
                info['images_age'] = time.time() - data.get('cached_at', 0)
        
        # Check categories cache
        if os.path.exists(self.categories_file):
            data = self._load_from_cache(self.categories_file)
            if data:
                info['categories_count'] = len(data.get('categories', {}))
                info['categories_age'] = time.time() - data.get('cached_at', 0)
        
        # Check if cache is valid
        info['cache_valid'] = (self._is_cache_valid(self.images_file) and 
                              self._is_cache_valid(self.categories_file))
        
        return info
    
    def clear_cache(self) -> bool:
        """Clear all cache files"""
        try:
            if os.path.exists(self.images_file):
                os.remove(self.images_file)
            if os.path.exists(self.categories_file):
                os.remove(self.categories_file)
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def refresh_cache(self, images: List[Dict], categories: Dict) -> bool:
        """Refresh cache with new data"""
        try:
            # Save new data
            images_saved = self.save_images(images)
            categories_saved = self.save_categories(categories)
            
            return images_saved and categories_saved
        except Exception as e:
            logger.error(f"Error refreshing cache: {e}")
            return False

# Global cache instance
docker_hub_cache = DockerHubCache()
