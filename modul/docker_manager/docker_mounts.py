"""
Docker Mounts Manager
Container mount bilgilerini yönetir
"""

import docker
import json
from datetime import datetime

def get_docker_client():
    """Docker client oluştur"""
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception as e:
        print(f"Docker bağlantı hatası: {e}")
        return None

def get_container_mounts(container_id):
    """Container mount bilgilerini al"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        mounts = container.attrs.get('Mounts', [])
        
        return {'success': True, 'mounts': mounts}
        
    except Exception as e:
        print(f"Mounts error: {e}")
        return {'success': False, 'message': str(e)}

def get_container_volumes(container_id):
    """Container volume bilgilerini al"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        volumes = container.attrs.get('Mounts', [])
        
        # Sadece volume mount'ları filtrele
        volume_mounts = [mount for mount in volumes if mount.get('Type') == 'volume']
        
        return {'success': True, 'volumes': volume_mounts}
        
    except Exception as e:
        print(f"Volumes error: {e}")
        return {'success': False, 'message': str(e)}

def get_container_bind_mounts(container_id):
    """Container bind mount bilgilerini al"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        mounts = container.attrs.get('Mounts', [])
        
        # Sadece bind mount'ları filtrele
        bind_mounts = [mount for mount in mounts if mount.get('Type') == 'bind']
        
        return {'success': True, 'bind_mounts': bind_mounts}
        
    except Exception as e:
        print(f"Bind mounts error: {e}")
        return {'success': False, 'message': str(e)}

def format_mount_data(mounts):
    """Mount verisini formatla"""
    formatted_mounts = []
    
    for mount in mounts:
        formatted_mount = {
            'type': mount.get('Type', ''),
            'source': mount.get('Source', ''),
            'destination': mount.get('Destination', ''),
            'mode': mount.get('Mode', ''),
            'rw': mount.get('RW', False),
            'propagation': mount.get('Propagation', ''),
            'name': mount.get('Name', ''),
            'driver': mount.get('Driver', ''),
            'options': mount.get('Options', {})
        }
        formatted_mounts.append(formatted_mount)
    
    return formatted_mounts

def get_mount_info(container_id):
    """Container mount bilgilerini detaylı al"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        mounts = container.attrs.get('Mounts', [])
        
        # Mount türlerine göre grupla
        volume_mounts = []
        bind_mounts = []
        tmpfs_mounts = []
        
        for mount in mounts:
            mount_type = mount.get('Type', '')
            if mount_type == 'volume':
                volume_mounts.append(mount)
            elif mount_type == 'bind':
                bind_mounts.append(mount)
            elif mount_type == 'tmpfs':
                tmpfs_mounts.append(mount)
        
        return {
            'success': True,
            'all_mounts': mounts,
            'volume_mounts': volume_mounts,
            'bind_mounts': bind_mounts,
            'tmpfs_mounts': tmpfs_mounts,
            'total_count': len(mounts)
        }
        
    except Exception as e:
        print(f"Mount info error: {e}")
        return {'success': False, 'message': str(e)}
