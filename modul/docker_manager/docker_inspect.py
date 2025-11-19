"""
Docker Inspect Manager
Container inspect bilgilerini yönetir
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

def get_container_inspect(container_id):
    """Container inspect bilgilerini al"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        inspect_data = container.attrs
        
        return {'success': True, 'inspect': inspect_data}
        
    except Exception as e:
        print(f"Inspect error: {e}")
        return {'success': False, 'message': str(e)}

def get_container_config(container_id):
    """Container config bilgilerini al"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        config = container.attrs.get('Config', {})
        
        return {'success': True, 'config': config}
        
    except Exception as e:
        print(f"Config error: {e}")
        return {'success': False, 'message': str(e)}

def get_container_state(container_id):
    """Container state bilgilerini al"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        state = container.attrs.get('State', {})
        
        return {'success': True, 'state': state}
        
    except Exception as e:
        print(f"State error: {e}")
        return {'success': False, 'message': str(e)}

def format_inspect_data(inspect_data):
    """Inspect verisini formatla"""
    formatted = {
        'id': inspect_data.get('Id', ''),
        'name': inspect_data.get('Name', '').lstrip('/'),
        'image': inspect_data.get('Config', {}).get('Image', ''),
        'status': inspect_data.get('State', {}).get('Status', ''),
        'created': inspect_data.get('Created', ''),
        'started_at': inspect_data.get('State', {}).get('StartedAt', ''),
        'finished_at': inspect_data.get('State', {}).get('FinishedAt', ''),
        'restart_count': inspect_data.get('RestartCount', 0),
        'platform': inspect_data.get('Platform', ''),
        'architecture': inspect_data.get('Architecture', ''),
        'config': inspect_data.get('Config', {}),
        'state': inspect_data.get('State', {}),
        'mounts': inspect_data.get('Mounts', []),
        'network_settings': inspect_data.get('NetworkSettings', {}),
        'host_config': inspect_data.get('HostConfig', {})
    }
    
    return formatted
