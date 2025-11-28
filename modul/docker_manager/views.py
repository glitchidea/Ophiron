from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
import json
import docker
import psutil
import time
import math
import subprocess
from datetime import datetime, timedelta
from .models import DockerLog, DockerSettings
import logging

# Logger setup
logger = logging.getLogger(__name__)

def log_docker_operation(container_name, action, status, message, user='Anonymous', ip_address=None, command='', details=None):
    """Log Docker operations to database"""
    try:
        settings = DockerSettings.get_global_settings()
        if settings.logging_enabled:
            DockerLog.objects.create(
                container_name=container_name,
                action=action,
                status=status,
                message=message,
                user=user,
                ip_address=ip_address,
                command=command,
                details=details or {}
            )
            logger.info(f"Docker operation logged: {container_name} - {action} - {status}")
    except Exception as e:
        logger.error(f"Failed to log Docker operation: {e}")

# Modüler Docker yöneticileri
from .docker_logs import get_container_logs
from .docker_inspect import get_container_inspect, format_inspect_data
from .docker_mounts import get_container_mounts, get_mount_info
from .docker_terminal import connect_container_terminal, execute_container_command
from .docker_files import get_container_files, get_file_content
from .docker_stats import get_container_stats, get_container_processes
from . import docker_cve_scanner


def get_docker_client():
    """Docker client oluştur"""
    try:
        client = docker.from_env()
        return client
    except Exception as e:
        print(f"Docker client oluşturulamadı: {e}")
        return None

def check_docker_update():
    """Docker update kontrolü"""
    try:
        import subprocess
        import re
        
        # Docker version kontrolü
        result = subprocess.run(['docker', 'version', '--format', '{{.Server.Version}}'], 
                               capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            current_version = result.stdout.strip()
            
            # Docker update kontrolü (basit versiyon)
            # Gerçek update kontrolü için Docker Hub API kullanılabilir
            return {
                'success': True,
                'has_update': False,  # Şimdilik False, gerçek kontrol eklenebilir
                'current_version': current_version,
                'latest_version': current_version,
                'message': 'Docker is up to date'
            }
        else:
            return {
                'success': False,
                'has_update': False,
                'message': 'Docker version check failed'
            }
            
    except Exception as e:
        return {
            'success': False,
            'has_update': False,
            'message': f'Update check failed: {str(e)}'
        }

def index(request):
    """Docker Manager ana sayfası - Container bölümü"""
    client = get_docker_client()
    containers = []
    
    # Docker update kontrolü
    update_info = check_docker_update()
    
    if client:
        try:
            # Tüm containerları al
            docker_containers = client.containers.list(all=True)
            
            for container in docker_containers:
                # Container bilgilerini al
                container_info = {
                    'id': container.short_id,
                    'name': container.name,
                    'image': container.image.tags[0] if container.image.tags else container.image.short_id,
                    'image_id': container.image.short_id,  # Image ID'sini ekle
                    'status': container.status,
                    'ports': get_container_ports(container),
                    'lastStarted': get_container_start_time(container),
                    'created': container.attrs['Created'],
                    'state': container.attrs['State']
                }
                containers.append(container_info)
                
        except Exception as e:
            print(f"Container bilgileri alınamadı: {e}")
    
    # JavaScript translations for modals
    js_translations = {
        'Container ID copied to clipboard': _('Container ID copied to clipboard'),
        'Container': _('Container'),
        'durdurulsun mu?': _('durdurulsun mu?'),
        'durduruluyor...': _('durduruluyor...'),
        'durduruldu': _('durduruldu'),
        'başlatılıyor...': _('başlatılıyor...'),
        'başlatıldı': _('başlatıldı'),
        'silinsin mi? Bu işlem geri alınamaz.': _('silinsin mi? Bu işlem geri alınamaz.'),
        'siliniyor...': _('siliniyor...'),
        'silindi': _('silindi'),
        'yeniden başlatılsın mı?': _('yeniden başlatılsın mı?'),
        'yeniden başlatılıyor...': _('yeniden başlatılıyor...'),
        'yeniden başlatıldı': _('yeniden başlatıldı'),
        'Hata:': _('Hata:'),
        'More options for': _('More options for'),
        'Opening terminal...': _('Opening terminal...'),
        'Are you sure you want to restart Docker? This will stop all running containers.': _('Are you sure you want to restart Docker? This will stop all running containers.'),
        'Restarting Docker...': _('Restarting Docker...'),
        'Docker service restarted successfully': _('Docker service restarted successfully'),
        'Showing': _('Showing'),
        'items': _('items')
    }
    
    context = {
        'containers': containers,
        'docker_running': client is not None,
        'update_info': update_info,
        'js_translations': json.dumps(js_translations)
    }
    
    return render(request, 'modules/docker_manager/index.html', context)

def get_container_ports(container):
    """Container port bilgilerini al"""
    ports = []
    if container.attrs.get('NetworkSettings', {}).get('Ports'):
        for container_port, host_bindings in container.attrs['NetworkSettings']['Ports'].items():
            if host_bindings:
                for binding in host_bindings:
                    host_port = binding.get('HostPort', '')
                    if host_port:
                        ports.append(f"{host_port}:{container_port}")
    return ', '.join(ports) if ports else ''

def get_container_start_time(container):
    """Container başlama zamanını al"""
    try:
        started_at = container.attrs['State'].get('StartedAt')
        if started_at and started_at != '0001-01-01T00:00:00Z':
            # ISO format tarihini parse et
            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            now = datetime.now(start_time.tzinfo)
            diff = now - start_time
            
            if diff.days > 0:
                return f"{diff.days} days ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hours ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minutes ago"
            else:
                return "Just now"
        return "Unknown"
    except:
        return "Unknown"

# CPU ve Memory sütunları kaldırıldı - gerçek veriler gösterilemiyor

def containers(request):
    """Container yönetimi sayfası"""
    return render(request, 'modules/docker_manager/containers.html')

def container_detail(request, container_id):
    """Container detay sayfası"""
    try:
        client = get_docker_client()
        if not client:
            return render(request, 'modules/docker_manager/container_detail.html', {
                'container': None,
                'docker_running': False
            })
        
        # Container bilgilerini al
        container = client.containers.get(container_id)
        
        # Container bilgilerini hazırla
        container_info = {
            'id': container.short_id,
            'name': container.name,
            'image': container.image.tags[0] if container.image.tags else container.image.short_id,
            'status': container.status,
            'ports': get_container_ports(container),
            'lastStarted': get_container_start_time(container),
            'created': container.attrs['Created'],
            'state': container.attrs['State']
        }
        
        return render(request, 'modules/docker_manager/container_detail.html', {
            'container': container_info,
            'docker_running': True
        })
        
    except Exception as e:
        return render(request, 'modules/docker_manager/container_detail.html', {
            'container': None,
            'docker_running': False,
            'error': str(e)
        })

def images(request):
    """Docker Images sayfası"""
    client = get_docker_client()
    images = []
    
    # Docker update kontrolü
    update_info = check_docker_update()
    
    if client:
        try:
            # Tüm imageleri al
            docker_images = client.images.list(all=True)
            
            for image in docker_images:
                # Image bilgilerini al
                image_info = {
                    'id': image.short_id,
                    'name': image.tags[0].split(':')[0] if image.tags else '<none>',
                    'tag': image.tags[0].split(':')[1] if image.tags and ':' in image.tags[0] else '<none>',
                    'size': format_bytes(image.attrs['Size']),
                    'created': format_datetime(image.attrs['Created']),
                    'labels': image.attrs.get('Labels', {}),
                    'attrs': image.attrs
                }
                images.append(image_info)
                
        except Exception as e:
            print(f"Image bilgileri alınamadı: {e}")
    
    context = {
        'images': images,
        'docker_running': client is not None,
        'update_info': update_info
    }
    
    return render(request, 'modules/docker_manager/images.html', context)

def volumes(request):
    """Docker Volumes sayfası"""
    client = get_docker_client()
    volumes = []
    
    # Docker update kontrolü
    update_info = check_docker_update()
    
    if client:
        try:
            # Tüm volume'ları al
            docker_volumes = client.volumes.list()
            
            for volume in docker_volumes:
                volume_info = {
                    'name': volume.name,
                    'driver': volume.attrs.get('Driver', 'local'),
                    'size': format_bytes(volume.attrs.get('Size', 0)),
                    'created': format_datetime(volume.attrs.get('CreatedAt', '')),
                    'attrs': volume.attrs
                }
                volumes.append(volume_info)
                
        except Exception as e:
            print(f"Volume bilgileri alınamadı: {e}")
    
    context = {
        'volumes': volumes,
        'docker_running': client is not None,
        'update_info': update_info
    }
    
    return render(request, 'modules/docker_manager/volumes.html', context)



def docker_scout(request):
    """Docker Scout sayfası"""
    return render(request, 'modules/docker_manager/docker_scout.html')

def extensions(request):
    """Extensions yönetimi sayfası"""
    return render(request, 'modules/docker_manager/extensions.html')

def hubs(request):
    """Docker Hubs yönetimi sayfası"""
    try:
        from .docker_hub_cache import docker_hub_cache
        
        # Get cached data
        images = docker_hub_cache.get_cached_images()
        cache_info = docker_hub_cache.get_cache_info()
        
        context = {
            'images': images,
            'total_images': len(images),
            'cache_info': cache_info
        }
        
        return render(request, 'modules/docker_manager/hubs.html', context)
        
    except Exception as e:
        logger.error(f"Hubs view error: {e}")
        context = {
            'images': [],
            'total_images': 0,
            'cache_info': {'cache_valid': False}
        }
        return render(request, 'modules/docker_manager/hubs.html', context)

def search_hub(request):
    """Docker Hub arama"""
    from .docker_hub_views import search_hub as search_view
    return search_view(request)

def get_repository_details(request, namespace, name):
    """Repository detaylarını al"""
    from .docker_hub_views import get_repository_details as details_view
    return details_view(request, namespace, name)

def get_repository_tags(request, namespace, name):
    """Repository tag'lerini al"""
    from .docker_hub_views import get_repository_tags as tags_view
    return tags_view(request, namespace, name)

def pull_image(request):
    """Docker imajını pull et"""
    from .docker_hub_views import pull_image as pull_view
    return pull_view(request)

def clear_cache(request):
    """Cache'i temizle"""
    from .docker_hub_views import clear_cache as clear_view
    return clear_view(request)

def get_cache_info(request):
    """Cache bilgilerini al"""
    from .docker_hub_views import get_cache_info as cache_info_view
    return cache_info_view(request)

# API Endpoints for Container Operations
def container_stop(request, container_id):
    """Container'ı durdur"""
    if request.method == 'POST':
        try:
            client = get_docker_client()
            if client:
                container = client.containers.get(container_id)
                container.stop()
                return JsonResponse({'success': True, 'message': f'Container {container_id} stopped'})
            else:
                return JsonResponse({'success': False, 'message': 'Docker not available'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def container_start(request, container_id):
    """Container'ı başlat"""
    if request.method == 'POST':
        try:
            client = get_docker_client()
            if client:
                container = client.containers.get(container_id)
                container.start()
                
                # Log the operation
                log_docker_operation(
                    container_name=container.name,
                    action='start',
                    status='success',
                    message=f'Container {container.name} started successfully',
                    user=request.user.username if request.user.is_authenticated else 'Anonymous',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={'container_id': container_id}
                )
                
                return JsonResponse({'success': True, 'message': f'Container {container_id} started'})
            else:
                return JsonResponse({'success': False, 'message': 'Docker not available'})
        except Exception as e:
            # Log the error
            log_docker_operation(
                container_name=container_id,
                action='start',
                status='error',
                message=f'Failed to start container: {str(e)}',
                user=request.user.username if request.user.is_authenticated else 'Anonymous',
                ip_address=request.META.get('REMOTE_ADDR'),
                details={'error': str(e)}
            )
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def container_remove(request, container_id):
    """Container'ı sil"""
    if request.method == 'POST':
        try:
            client = get_docker_client()
            if client:
                container = client.containers.get(container_id)
                container.remove(force=True)
                return JsonResponse({'success': True, 'message': f'Container {container_id} removed'})
            else:
                return JsonResponse({'success': False, 'message': 'Docker not available'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def container_restart(request, container_id):
    """Container'ı yeniden başlat"""
    if request.method == 'POST':
        try:
            client = get_docker_client()
            if client:
                container = client.containers.get(container_id)
                container.restart()
                return JsonResponse({'success': True, 'message': f'Container {container_id} restarted'})
            else:
                return JsonResponse({'success': False, 'message': 'Docker not available'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

# Container Detail API Endpoints
def container_logs(request, container_id):
    """Container loglarını al"""
    # Tüm logları al (tail parametresi yok)
    result = get_container_logs(container_id, tail=None)
    return JsonResponse(result)

def container_inspect(request, container_id):
    """Container inspect bilgilerini al"""
    result = get_container_inspect(container_id)
    return JsonResponse(result)

def container_mounts(request, container_id):
    """Container mount bilgilerini al"""
    result = get_mount_info(container_id)
    return JsonResponse(result)


def container_files(request, container_id):
    """Container dosya listesi"""
    path = request.GET.get('path', '/')
    result = get_container_files(container_id, path)
    return JsonResponse(result)

def container_files_content(request, container_id):
    """Container dosya içeriği"""
    path = request.GET.get('path', '')
    result = get_file_content(container_id, path)
    return JsonResponse(result)

def container_stats(request, container_id):
    """Container istatistikleri"""
    result = get_container_stats(container_id)
    return JsonResponse(result)


def container_cve_scan(request, container_id):
    """Container içindeki paketler için CVE taraması yap"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

    try:
        scan_result = docker_cve_scanner.scan_container_cves(container_id)
        status = 200 if scan_result.get("success") else 400
        return JsonResponse(scan_result, status=status)
    except Exception as exc:
        logger.error(f"Container CVE scan error for {container_id}: {exc}", exc_info=True)
        return JsonResponse(
            {
                'success': False,
                'error': str(exc),
            },
            status=500,
        )

def format_bytes(bytes_val):
    """Bytes'ı okunabilir formata çevir"""
    if bytes_val == 0:
        return '0 B'
    k = 1024
    sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    i = int(math.floor(math.log(bytes_val) / math.log(k)))
    return f"{bytes_val / (k ** i):.1f} {sizes[i]}"

def format_datetime(dt_string):
    """Datetime string'ini formatla"""
    try:
        if dt_string:
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        return 'Unknown'
    except Exception as e:
        print(f"Datetime format error: {e}")
        return 'Unknown'

# Volume API Endpoints
def volume_inspect(request, volume_name):
    """Volume inspect data"""
    try:
        client = get_docker_client()
        if not client:
            return JsonResponse({'success': False, 'message': 'Docker not available'})
        
        volume = client.volumes.get(volume_name)
        inspect_data = volume.attrs
        
        return JsonResponse({'success': True, 'inspect': inspect_data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def volume_delete(request, volume_name):
    """Volume sil"""
    if request.method == 'POST':
        try:
            client = get_docker_client()
            if not client:
                return JsonResponse({'success': False, 'message': 'Docker not available'})
            
            volume = client.volumes.get(volume_name)
            volume.remove()
            
            return JsonResponse({'success': True, 'message': 'Volume deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def volume_create(request):
    """Volume oluştur"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            driver = data.get('driver', 'local')
            labels = data.get('labels', {})
            options = data.get('options', {})
            
            client = get_docker_client()
            if not client:
                return JsonResponse({'success': False, 'message': 'Docker not available'})
            
            # Create volume
            volume = client.volumes.create(
                name=name,
                driver=driver,
                labels=labels,
                driver_opts=options
            )
            
            return JsonResponse({
                'success': True, 
                'message': f'Volume {volume.name} created successfully',
                'volume_name': volume.name
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def volume_prune(request):
    """Unused volume'ları temizle"""
    if request.method == 'POST':
        try:
            client = get_docker_client()
            if not client:
                return JsonResponse({'success': False, 'message': 'Docker not available'})
            
            # Prune volumes
            result = client.volumes.prune()
            
            return JsonResponse({
                'success': True, 
                'message': 'Volumes pruned successfully',
                'pruned_count': len(result.get('VolumesDeleted', []))
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def volume_detail(request, volume_name):
    """Volume detay sayfası"""
    client = get_docker_client()
    
    if not client:
        return render(request, 'modules/docker_manager/volume_detail.html', {
            'volume': None,
            'docker_running': False,
            'error': 'Docker is not running'
        })
    
    try:
        volume = client.volumes.get(volume_name)
        
        volume_info = {
            'name': volume.name,
            'driver': volume.attrs.get('Driver', 'local'),
            'size': format_bytes(volume.attrs.get('Size', 0)),
            'created': format_datetime(volume.attrs.get('CreatedAt', '')),
            'mountpoint': volume.attrs.get('Mountpoint', ''),
            'labels': volume.attrs.get('Labels', {}),
            'options': volume.attrs.get('Options', {}),
            'attrs': volume.attrs
        }
        
        return render(request, 'modules/docker_manager/volume_detail.html', {
            'volume': volume_info,
            'docker_running': True
        })
        
    except Exception as e:
        return render(request, 'modules/docker_manager/volume_detail.html', {
            'volume': None,
            'docker_running': True,
            'error': str(e)
        })

# Image API Endpoints
def image_delete(request, image_id):
    """Image sil"""
    if request.method == 'POST':
        try:
            client = get_docker_client()
            if not client:
                return JsonResponse({'success': False, 'message': 'Docker not available'})
            
            image = client.images.get(image_id)
            client.images.remove(image_id, force=True)
            
            return JsonResponse({'success': True, 'message': 'Image deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def image_pull(request):
    """Image pull"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_name = data.get('image', '')
            
            if not image_name:
                return JsonResponse({'success': False, 'message': 'Image name required'})
            
            client = get_docker_client()
            if not client:
                return JsonResponse({'success': False, 'message': 'Docker not available'})
            
            # Pull image
            client.images.pull(image_name)
            
            return JsonResponse({'success': True, 'message': f'Image {image_name} pulled successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def image_build(request):
    """Image build"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            dockerfile = data.get('dockerfile', '')
            image_name = data.get('image', '')
            
            if not dockerfile or not image_name:
                return JsonResponse({'success': False, 'message': 'Dockerfile path and image name required'})
            
            client = get_docker_client()
            if not client:
                return JsonResponse({'success': False, 'message': 'Docker not available'})
            
            # Build image
            image, build_logs = client.images.build(
                path=dockerfile,
                tag=image_name,
                rm=True
            )
            
            return JsonResponse({'success': True, 'message': f'Image {image_name} built successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def image_run(request):
    """Image'dan container çalıştır"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_id = data.get('image', '')
            name = data.get('name', '')
            ports = data.get('ports', '')
            env = data.get('env', [])
            
            if not image_id:
                return JsonResponse({'success': False, 'message': 'Image ID required'})
            
            client = get_docker_client()
            if not client:
                return JsonResponse({'success': False, 'message': 'Docker not available'})
            
            # Port mapping
            port_bindings = {}
            if ports:
                try:
                    host_port, container_port = ports.split(':')
                    port_bindings[container_port] = int(host_port)
                except:
                    pass
            
            # Environment variables
            environment = {}
            for env_var in env:
                if '=' in env_var:
                    key, value = env_var.split('=', 1)
                    environment[key] = value
            
            # Run container
            container = client.containers.run(
                image_id,
                name=name if name else None,
                ports=port_bindings,
                environment=environment,
                detach=True
            )
            
            return JsonResponse({
                'success': True, 
                'message': f'Container {container.name} started successfully',
                'container_id': container.short_id
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def format_bytes(bytes):
    """Bytes'ı human readable formata çevir"""
    if bytes == 0:
        return '0 B'
    k = 1024
    sizes = ['B', 'KB', 'MB', 'GB']
    i = int(math.floor(math.log(bytes) / math.log(k)))
    return f"{bytes / (k ** i):.1f} {sizes[i]}"

def image_detail(request, image_id):
    """Image detay sayfası"""
    client = get_docker_client()
    
    if not client:
        return render(request, 'modules/docker_manager/image_detail.html', {
            'image': None,
            'docker_running': False,
            'error': 'Docker is not running'
        })
    
    try:
        # Önce image_id ile dene
        try:
            image = client.images.get(image_id)
        except:
            # Eğer bulunamazsa, tüm imageleri listele ve isimle ara
            images = client.images.list(all=True)
            image = None
            for img in images:
                if img.short_id == image_id or image_id in img.short_id:
                    image = img
                    break
                # Tag ile de ara
                for tag in img.tags:
                    if image_id in tag:
                        image = img
                        break
                if image:
                    break
            
            if not image:
                raise Exception(f"Image not found: {image_id}")
        
        image_info = {
            'id': image.short_id,
            'name': image.tags[0].split(':')[0] if image.tags else '<none>',
            'tag': image.tags[0].split(':')[1] if image.tags and ':' in image.tags[0] else '<none>',
            'size': format_bytes(image.attrs['Size']),
            'created': format_datetime(image.attrs['Created']),
            'labels': image.attrs.get('Labels', {}),
            'attrs': image.attrs
        }
        
        return render(request, 'modules/docker_manager/image_detail.html', {
            'image': image_info,
            'docker_running': True
        })
        
    except Exception as e:
        return render(request, 'modules/docker_manager/image_detail.html', {
            'image': None,
            'docker_running': True,
            'error': str(e)
        })

def image_inspect(request, image_id):
    """Image inspect data"""
    try:
        client = get_docker_client()
        if not client:
            return JsonResponse({'success': False, 'message': 'Docker not available'})
        
        image = client.images.get(image_id)
        inspect_data = image.attrs
        
        return JsonResponse({'success': True, 'inspect': inspect_data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def image_history(request, image_id):
    """Image history data"""
    try:
        client = get_docker_client()
        if not client:
            return JsonResponse({'success': False, 'message': 'Docker not available'})
        
        image = client.images.get(image_id)
        history = image.history()
        
        return JsonResponse({'success': True, 'history': history})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def image_logs(request, image_id):
    """Image logs data"""
    try:
        client = get_docker_client()
        if not client:
            return JsonResponse({'success': False, 'message': 'Docker not available'})
        
        # Image'ın container'larını bul
        containers = client.containers.list(all=True, filters={'ancestor': image_id})
        
        if not containers:
            return JsonResponse({
                'success': True,
                'logs': 'No containers found for this image'
            })
        
        # İlk container'ın loglarını al
        container = containers[0]
        logs = container.logs().decode('utf-8')
        
        return JsonResponse({
            'success': True,
            'logs': logs
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

# ===== BUILDS MANAGEMENT API ENDPOINTS =====

def build_image(request):
    """Build Docker image from Dockerfile"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            dockerfile_path = data.get('dockerfile_path', '')
            image_name = data.get('image_name', '')
            tag = data.get('tag', 'latest')
            build_args = data.get('build_args', {})
            no_cache = data.get('no_cache', False)
            
            if not dockerfile_path or not image_name:
                return JsonResponse({'success': False, 'message': 'Dockerfile path and image name required'})
            
            client = get_docker_client()
            if not client:
                return JsonResponse({'success': False, 'message': 'Docker not available'})
            
            # Full image name with tag
            full_image_name = f"{image_name}:{tag}" if tag else image_name
            
            # Build image with progress tracking
            build_logs = []
            try:
                image, build_logs = client.images.build(
                    path=dockerfile_path,
                    tag=full_image_name,
                    rm=True,
                    nocache=no_cache,
                    buildargs=build_args,
                    decode=True
                )
                
                # Log the build operation
                log_docker_operation(
                    container_name='Build Process',
                    action='build',
                    status='success',
                    message=f'Image {full_image_name} built successfully',
                    user=request.user.username if request.user.is_authenticated else 'Anonymous',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={
                        'image_name': full_image_name,
                        'dockerfile_path': dockerfile_path,
                        'build_args': build_args
                    }
                )
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Image {full_image_name} built successfully',
                    'image_id': image.short_id,
                    'build_logs': build_logs
                })
                
            except Exception as build_error:
                # Log the build failure
                log_docker_operation(
                    container_name='Build Process',
                    action='build',
                    status='error',
                    message=f'Build failed: {str(build_error)}',
                    user=request.user.username if request.user.is_authenticated else 'Anonymous',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={
                        'image_name': full_image_name,
                        'dockerfile_path': dockerfile_path,
                        'error': str(build_error)
                    }
                )
                return JsonResponse({'success': False, 'message': str(build_error)})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def build_from_git(request):
    """Build Docker image from Git repository"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            git_url = data.get('git_url', '')
            image_name = data.get('image_name', '')
            tag = data.get('tag', 'latest')
            dockerfile_path = data.get('dockerfile_path', 'Dockerfile')
            build_args = data.get('build_args', {})
            
            if not git_url or not image_name:
                return JsonResponse({'success': False, 'message': 'Git URL and image name required'})
            
            client = get_docker_client()
            if not client:
                return JsonResponse({'success': False, 'message': 'Docker not available'})
            
            # Full image name with tag
            full_image_name = f"{image_name}:{tag}" if tag else image_name
            
            # Build from Git repository
            image, build_logs = client.images.build(
                path=git_url,
                dockerfile=dockerfile_path,
                tag=full_image_name,
                rm=True,
                buildargs=build_args,
                decode=True
            )
            
            # Log the build operation
            log_docker_operation(
                container_name='Build Process',
                action='build_from_git',
                status='success',
                message=f'Image {full_image_name} built from Git successfully',
                user=request.user.username if request.user.is_authenticated else 'Anonymous',
                ip_address=request.META.get('REMOTE_ADDR'),
                details={
                    'image_name': full_image_name,
                    'git_url': git_url,
                    'dockerfile_path': dockerfile_path
                }
            )
            
            return JsonResponse({
                'success': True, 
                'message': f'Image {full_image_name} built from Git successfully',
                'image_id': image.short_id,
                'build_logs': build_logs
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def get_build_logs(request, build_id):
    """Get build logs for a specific build"""
    try:
        client = get_docker_client()
        if not client:
            return JsonResponse({'success': False, 'message': 'Docker not available'})
        
        # Get image by ID
        image = client.images.get(build_id)
        
        # Get image history (build steps)
        history = image.history()
        
        return JsonResponse({
            'success': True, 
            'history': history,
            'image_info': {
                'id': image.short_id,
                'tags': image.tags,
                'created': image.attrs['Created'],
                'size': image.attrs['Size']
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def delete_build(request, build_id):
    """Delete a build (Docker image)"""
    if request.method == 'DELETE':
        try:
            client = get_docker_client()
            if not client:
                return JsonResponse({'success': False, 'message': 'Docker not available'})
            
            # Get image info before deletion
            image = client.images.get(build_id)
            image_name = image.tags[0] if image.tags else build_id
            
            # Remove image
            client.images.remove(build_id, force=True)
            
            # Log the deletion
            log_docker_operation(
                container_name='Build Management',
                action='delete_build',
                status='success',
                message=f'Build {image_name} deleted successfully',
                user=request.user.username if request.user.is_authenticated else 'Anonymous',
                ip_address=request.META.get('REMOTE_ADDR'),
                details={'build_id': build_id, 'image_name': image_name}
            )
            
            return JsonResponse({
                'success': True, 
                'message': f'Build {image_name} deleted successfully'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def build_inspect(request, build_id):
    """Get detailed build information"""
    try:
        client = get_docker_client()
        if not client:
            return JsonResponse({'success': False, 'message': 'Docker not available'})
        
        image = client.images.get(build_id)
        
        build_info = {
            'id': image.short_id,
            'tags': image.tags,
            'created': format_datetime(image.attrs['Created']),
            'size': format_bytes(image.attrs['Size']),
            'architecture': image.attrs.get('Architecture', 'unknown'),
            'os': image.attrs.get('Os', 'unknown'),
            'labels': image.attrs.get('Labels', {}),
            'history': image.history(),
            'attrs': image.attrs
        }
        
        return JsonResponse({'success': True, 'build_info': build_info})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def build_prune(request):
    """Clean up unused build cache and dangling images"""
    if request.method == 'POST':
        try:
            client = get_docker_client()
            if not client:
                return JsonResponse({'success': False, 'message': 'Docker not available'})
            
            # Prune build cache
            prune_result = client.images.prune()
            
            # Log the prune operation
            log_docker_operation(
                container_name='Build Management',
                action='build_prune',
                status='success',
                message=f'Build cache pruned successfully',
                user=request.user.username if request.user.is_authenticated else 'Anonymous',
                ip_address=request.META.get('REMOTE_ADDR'),
                details=prune_result
            )
            
            return JsonResponse({
                'success': True, 
                'message': 'Build cache pruned successfully',
                'pruned_data': prune_result
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


# ===== LOGGING API ENDPOINTS =====

@require_http_methods(["GET"])
@login_required
def get_logging_status(request):
    """Get Docker Manager logging status"""
    try:
        settings = DockerSettings.get_global_settings()
        return JsonResponse({
            'success': True,
            'logging_enabled': settings.logging_enabled,
            'log_retention_days': settings.log_retention_days,
            'realtime_logging': settings.realtime_logging,
            'last_modified_by': settings.last_modified_by or 'N/A'
        })
    except Exception as e:
        logger.error(f"Error getting Docker logging status: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["POST"])
@login_required
def toggle_logging(request):
    """Toggle Docker Manager logging"""
    try:
        data = json.loads(request.body)
        settings = DockerSettings.get_global_settings()
        
        # Update logging settings
        if 'logging_enabled' in data:
            settings.logging_enabled = bool(data['logging_enabled'])
        
        if 'log_retention_days' in data:
            settings.log_retention_days = int(data['log_retention_days'])
        
        if 'realtime_logging' in data:
            settings.realtime_logging = bool(data['realtime_logging'])
        
        settings.last_modified_by = request.user.username
        settings.save()
        
        # Log the logging toggle operation
        log_docker_operation(
            container_name='Docker Manager',
            action='logs',
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
            'log_retention_days': settings.log_retention_days,
            'realtime_logging': settings.realtime_logging
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error toggling Docker logging: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# Docker Hub Refresh Functions
@csrf_exempt
def refresh_all_data(request):
    """Tüm verileri yenile ve cache'i güncelle"""
    try:
        from .docker_hub_api import DockerHubAPI
        from .docker_hub_cache import docker_hub_cache
        
        api = DockerHubAPI()
        
        # Fetch fresh data
        images = api.get_all_official_images()
        categories = api.get_categories()
        
        # Update cache
        if images and 'results' in images:
            cache_saved = docker_hub_cache.save_images(images['results'])
            if cache_saved:
                return JsonResponse({
                    'success': True,
                    'message': f'Cache updated with {len(images["results"])} images',
                    'images_loaded': len(images['results']),
                    'categories_loaded': len(categories.get('products', [])) + len(categories.get('categories', []))
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Failed to save to cache'
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to fetch images'
            })
            
    except Exception as e:
        logger.error(f"Refresh all data error: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })

def get_refresh_status(request):
    """Refresh durumunu al"""
    from .docker_hub_views import get_refresh_status as status_view
    return status_view(request)

@login_required
def docker_service_restart(request):
    """Docker servisini yeniden başlat"""
    if request.method == 'POST':
        try:
            # Docker servisini restart et
            result = subprocess.run(
                ['sudo', 'systemctl', 'restart', 'docker'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Log işlemi
                log_docker_operation(
                    container_name='docker-service',
                    action='restart',
                    status='success',
                    message='Docker service restarted successfully',
                    user=request.user.username if request.user.is_authenticated else 'Anonymous',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    command='systemctl restart docker'
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Docker service restarted successfully'
                })
            else:
                error_message = result.stderr or result.stdout or 'Unknown error'
                log_docker_operation(
                    container_name='docker-service',
                    action='restart',
                    status='failed',
                    message=f'Docker service restart failed: {error_message}',
                    user=request.user.username if request.user.is_authenticated else 'Anonymous',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    command='systemctl restart docker',
                    details={'error': error_message}
                )
                
                return JsonResponse({
                    'success': False,
                    'message': f'Failed to restart Docker service: {error_message}'
                })
                
        except subprocess.TimeoutExpired:
            error_message = 'Docker restart operation timed out'
            log_docker_operation(
                container_name='docker-service',
                action='restart',
                status='failed',
                message=error_message,
                user=request.user.username if request.user.is_authenticated else 'Anonymous',
                ip_address=request.META.get('REMOTE_ADDR'),
                command='systemctl restart docker'
            )
            return JsonResponse({
                'success': False,
                'message': error_message
            })
        except Exception as e:
            error_message = str(e)
            log_docker_operation(
                container_name='docker-service',
                action='restart',
                status='failed',
                message=f'Docker service restart error: {error_message}',
                user=request.user.username if request.user.is_authenticated else 'Anonymous',
                ip_address=request.META.get('REMOTE_ADDR'),
                command='systemctl restart docker'
            )
            return JsonResponse({
                'success': False,
                'message': f'Error: {error_message}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })