"""
Docker Pull Manager
Handles Docker image pulling operations
"""

import docker
import logging
import threading
import time
from typing import Dict, Any, Optional
from django.http import JsonResponse

logger = logging.getLogger(__name__)

class DockerPullManager:
    """Docker image pull manager"""
    
    def __init__(self):
        """Initialize Docker client"""
        try:
            self.client = docker.from_env()
            self.pull_status = {}  # Track pull status
        except Exception as e:
            logger.error(f"Docker client initialization failed: {e}")
            self.client = None
    
    def pull_image(self, image_name: str, tag: str = "latest") -> Dict[str, Any]:
        """
        Pull Docker image
        
        Args:
            image_name: Name of the image to pull
            tag: Tag of the image (default: latest)
            
        Returns:
            Dict with success status and message
        """
        if not self.client:
            return {
                'success': False,
                'message': 'Docker client not available'
            }
        
        full_image_name = f"{image_name}:{tag}" if tag != "latest" else image_name
        
        try:
            logger.info(f"Starting to pull image: {full_image_name}")
            
            # Start pull in background thread
            pull_thread = threading.Thread(
                target=self._pull_image_background,
                args=(full_image_name,)
            )
            pull_thread.daemon = True
            pull_thread.start()
            
            # Mark as pulling
            self.pull_status[full_image_name] = {
                'status': 'pulling',
                'start_time': time.time(),
                'progress': 0
            }
            
            return {
                'success': True,
                'message': f'Image {full_image_name} is being pulled in background',
                'image_name': full_image_name,
                'status': 'pulling'
            }
            
        except Exception as e:
            logger.error(f"Error starting pull for {full_image_name}: {e}")
            return {
                'success': False,
                'message': f'Failed to start pull: {str(e)}'
            }
    
    def _pull_image_background(self, full_image_name: str):
        """Pull image in background thread"""
        try:
            logger.info(f"Pulling image in background: {full_image_name}")
            
            # Pull the image
            image = self.client.images.pull(full_image_name)
            
            # Update status
            self.pull_status[full_image_name] = {
                'status': 'completed',
                'end_time': time.time(),
                'progress': 100,
                'image_id': image.id
            }
            
            logger.info(f"Successfully pulled image: {full_image_name}")
            
        except Exception as e:
            logger.error(f"Error pulling image {full_image_name}: {e}")
            self.pull_status[full_image_name] = {
                'status': 'failed',
                'end_time': time.time(),
                'error': str(e)
            }
    
    def get_pull_status(self, image_name: str) -> Dict[str, Any]:
        """
        Get pull status for an image
        
        Args:
            image_name: Name of the image
            
        Returns:
            Dict with pull status
        """
        if image_name not in self.pull_status:
            return {
                'success': False,
                'message': 'No pull operation found for this image'
            }
        
        status = self.pull_status[image_name]
        
        return {
            'success': True,
            'status': status['status'],
            'progress': status.get('progress', 0),
            'start_time': status.get('start_time'),
            'end_time': status.get('end_time'),
            'error': status.get('error')
        }
    
    def list_local_images(self) -> Dict[str, Any]:
        """
        List all local Docker images
        
        Returns:
            Dict with list of local images
        """
        if not self.client:
            return {
                'success': False,
                'message': 'Docker client not available'
            }
        
        try:
            images = self.client.images.list()
            
            image_list = []
            for img in images:
                tags = img.tags if img.tags else ['<none>']
                for tag in tags:
                    image_list.append({
                        'id': img.id,
                        'tags': tag,
                        'created': img.attrs['Created'],
                        'size': img.attrs['Size']
                    })
            
            return {
                'success': True,
                'images': image_list,
                'count': len(image_list)
            }
            
        except Exception as e:
            logger.error(f"Error listing local images: {e}")
            return {
                'success': False,
                'message': f'Failed to list images: {str(e)}'
            }
    
    def check_image_exists(self, image_name: str) -> bool:
        """
        Check if image exists locally
        
        Args:
            image_name: Name of the image
            
        Returns:
            True if image exists locally
        """
        if not self.client:
            return False
        
        try:
            self.client.images.get(image_name)
            return True
        except docker.errors.ImageNotFound:
            return False
        except Exception as e:
            logger.error(f"Error checking image {image_name}: {e}")
            return False

# Global instance
pull_manager = DockerPullManager()

def pull_image_view(request):
    """
    Django view for pulling Docker images
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Only POST method allowed'
        })
    
    try:
        import json
        data = json.loads(request.body)
        image_name = data.get('image_name', '')
        
        if not image_name:
            return JsonResponse({
                'success': False,
                'message': 'Image name is required'
            })
        
        # Check if image already exists
        if pull_manager.check_image_exists(image_name):
            return JsonResponse({
                'success': True,
                'message': f'Image {image_name} already exists locally',
                'status': 'exists'
            })
        
        # Start pull operation
        result = pull_manager.pull_image(image_name)
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error in pull_image_view: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })

def get_pull_status_view(request, image_name):
    """
    Django view for getting pull status
    """
    try:
        result = pull_manager.get_pull_status(image_name)
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error in get_pull_status_view: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })

def list_local_images_view(request):
    """
    Django view for listing local images
    """
    try:
        result = pull_manager.list_local_images()
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error in list_local_images_view: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })
