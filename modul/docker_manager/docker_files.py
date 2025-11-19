"""
Docker Files Manager
Container dosya sistemini yönetir
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

def get_container_files(container_id, path='/'):
    """Container dosya listesi"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        if container.status != 'running':
            return {'success': False, 'message': 'Container is not running'}
        
        # ls -la komutu çalıştır
        exec_result = container.exec_run(f'ls -la {path}', stdout=True, stderr=True)
        output = exec_result.output.decode('utf-8') if exec_result.output else ''
        
        if exec_result.exit_code != 0:
            return {'success': False, 'message': f'Path not accessible: {path}'}
        
        files = []
        lines = output.split('\n')
        
        for line in lines[1:]:  # İlk satırı atla (total)
            if line.strip():
                parts = line.split()
                if len(parts) >= 9:
                    # Dosya adını doğru şekilde al (8. parçadan sonrası)
                    file_name = ' '.join(parts[8:])
                    
                    # Path'i düzgün oluştur
                    if path == '/':
                        full_path = f"/{file_name}"
                    else:
                        full_path = f"{path.rstrip('/')}/{file_name}"
                    
                    file_info = {
                        'permissions': parts[0],
                        'links': parts[1],
                        'owner': parts[2],
                        'group': parts[3],
                        'size': parts[4],
                        'date': parts[5],
                        'time': parts[6],
                        'name': file_name,
                        'type': 'directory' if parts[0].startswith('d') else 'file',
                        'path': full_path
                    }
                    files.append(file_info)
        
        return {
            'success': True, 
            'files': files,
            'path': path,
            'total_count': len(files)
        }
        
    except Exception as e:
        print(f"Files error: {e}")
        return {'success': False, 'message': str(e)}

def get_file_content(container_id, file_path):
    """Container dosya içeriği"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        if container.status != 'running':
            return {'success': False, 'message': 'Container is not running'}
        
        # Dosya içeriğini al
        exec_result = container.exec_run(f'cat {file_path}', stdout=True, stderr=True)
        content = exec_result.output.decode('utf-8') if exec_result.output else ''
        
        if exec_result.exit_code != 0:
            return {'success': False, 'message': f'File not accessible: {file_path}'}
        
        return {
            'success': True,
            'content': content,
            'file_path': file_path,
            'size': len(content)
        }
        
    except Exception as e:
        print(f"File content error: {e}")
        return {'success': False, 'message': str(e)}

def get_file_info(container_id, file_path):
    """Container dosya bilgileri"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        if container.status != 'running':
            return {'success': False, 'message': 'Container is not running'}
        
        # stat komutu çalıştır
        exec_result = container.exec_run(f'stat {file_path}', stdout=True, stderr=True)
        output = exec_result.output.decode('utf-8') if exec_result.output else ''
        
        if exec_result.exit_code != 0:
            return {'success': False, 'message': f'File not found: {file_path}'}
        
        # stat çıktısını parse et
        lines = output.split('\n')
        file_info = {
            'path': file_path,
            'exists': True,
            'size': 0,
            'permissions': '',
            'owner': '',
            'group': '',
            'modified': '',
            'type': 'file'
        }
        
        for line in lines:
            if 'Size:' in line:
                file_info['size'] = line.split('Size:')[1].strip().split()[0]
            elif 'Access:' in line:
                file_info['permissions'] = line.split('Access:')[1].strip().split()[0]
            elif 'Uid:' in line:
                file_info['owner'] = line.split('Uid:')[1].strip().split()[0]
            elif 'Gid:' in line:
                file_info['group'] = line.split('Gid:')[1].strip().split()[0]
            elif 'Modify:' in line:
                file_info['modified'] = line.split('Modify:')[1].strip()
        
        return {'success': True, 'file_info': file_info}
        
    except Exception as e:
        print(f"File info error: {e}")
        return {'success': False, 'message': str(e)}

def get_directory_tree(container_id, path='/', max_depth=3):
    """Container dizin ağacı"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        if container.status != 'running':
            return {'success': False, 'message': 'Container is not running'}
        
        # find komutu ile ağaç yapısı
        exec_result = container.exec_run(
            f'find {path} -maxdepth {max_depth} -type d | head -20', 
            stdout=True, 
            stderr=True
        )
        output = exec_result.output.decode('utf-8') if exec_result.output else ''
        
        if exec_result.exit_code != 0:
            return {'success': False, 'message': f'Path not accessible: {path}'}
        
        directories = [line.strip() for line in output.split('\n') if line.strip()]
        
        return {
            'success': True,
            'directories': directories,
            'path': path,
            'max_depth': max_depth
        }
        
    except Exception as e:
        print(f"Directory tree error: {e}")
        return {'success': False, 'message': str(e)}

def search_files(container_id, search_term, path='/', file_type='all'):
    """Container'da dosya ara"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        if container.status != 'running':
            return {'success': False, 'message': 'Container is not running'}
        
        # find komutu ile arama
        if file_type == 'files':
            find_cmd = f'find {path} -name "*{search_term}*" -type f'
        elif file_type == 'directories':
            find_cmd = f'find {path} -name "*{search_term}*" -type d'
        else:
            find_cmd = f'find {path} -name "*{search_term}*"'
        
        exec_result = container.exec_run(find_cmd, stdout=True, stderr=True)
        output = exec_result.output.decode('utf-8') if exec_result.output else ''
        
        if exec_result.exit_code != 0:
            return {'success': False, 'message': f'Search failed: {search_term}'}
        
        files = [line.strip() for line in output.split('\n') if line.strip()]
        
        return {
            'success': True,
            'files': files,
            'search_term': search_term,
            'path': path,
            'file_type': file_type,
            'total_count': len(files)
        }
        
    except Exception as e:
        print(f"Search files error: {e}")
        return {'success': False, 'message': str(e)}
