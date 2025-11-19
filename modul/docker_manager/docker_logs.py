"""
Docker Logs Manager
Container loglarını yönetir
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

def get_container_logs(container_id, tail=None):
    """Container loglarını al"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        
        if container.status != 'running':
            return {'success': True, 'logs': []}
        
        try:
            # Tüm logları al (tail=None ise tüm loglar)
            if tail is None:
                logs = container.logs(timestamps=True).decode('utf-8')
            else:
                logs = container.logs(tail=tail, timestamps=True).decode('utf-8')
        except Exception as e:
            print(f"Logs alınamadı: {e}")
            return {'success': True, 'logs': []}
        
        log_lines = []
        for line in logs.split('\n'):
            if line.strip():
                if 'T' in line and 'Z' in line:
                    timestamp_end = line.find('Z') + 1
                    timestamp = line[:timestamp_end]
                    message = line[timestamp_end:].strip()
                else:
                    parts = line.split(' ', 1)
                    if len(parts) >= 2:
                        timestamp = parts[0]
                        message = parts[1]
                    else:
                        timestamp = ''
                        message = line
                
                log_lines.append({
                    'timestamp': timestamp,
                    'message': message,
                    'stream': 'stdout'
                })
        
        return {'success': True, 'logs': log_lines}
        
    except Exception as e:
        print(f"Logs error: {e}")
        return {'success': False, 'message': str(e)}

def get_container_logs_stream(container_id):
    """Container loglarını stream olarak al (real-time)"""
    try:
        client = get_docker_client()
        if not client:
            return None
        
        container = client.containers.get(container_id)
        
        if container.status != 'running':
            return None
        
        # Stream logs
        for line in container.logs(stream=True, follow=True, timestamps=True):
            yield line.decode('utf-8')
            
    except Exception as e:
        print(f"Stream logs error: {e}")
        return None

def parse_log_line(line):
    """Log satırını parse et"""
    if not line.strip():
        return None
    
    if 'T' in line and 'Z' in line:
        timestamp_end = line.find('Z') + 1
        timestamp = line[:timestamp_end]
        message = line[timestamp_end:].strip()
    else:
        parts = line.split(' ', 1)
        if len(parts) >= 2:
            timestamp = parts[0]
            message = parts[1]
        else:
            timestamp = ''
            message = line
    
    return {
        'timestamp': timestamp,
        'message': message,
        'stream': 'stdout'
    }
