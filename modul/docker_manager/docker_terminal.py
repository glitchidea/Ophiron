"""
Docker Terminal Manager
Container terminal işlemlerini yönetir
"""

import docker
import json
import subprocess
import threading
import time
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

def connect_container_terminal(container_id):
    """Container terminal bağlantısı"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        if container.status != 'running':
            return {'success': False, 'message': 'Container is not running'}
        
        return {'success': True, 'message': 'Terminal connected'}
        
    except Exception as e:
        print(f"Terminal connect error: {e}")
        return {'success': False, 'message': str(e)}

def execute_container_command(container_id, command):
    """Container'da komut çalıştır"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        if container.status != 'running':
            return {'success': False, 'message': 'Container is not running'}
        
        # Komutu çalıştır
        exec_result = container.exec_run(
            command, 
            stdout=True, 
            stderr=True,
            stdin=True,
            tty=True
        )
        
        output = exec_result.output.decode('utf-8') if exec_result.output else ''
        exit_code = exec_result.exit_code
        
        return {
            'success': True, 
            'output': output,
            'exit_code': exit_code,
            'command': command
        }
        
    except Exception as e:
        print(f"Command execution error: {e}")
        return {'success': False, 'message': str(e)}

def get_container_shell(container_id):
    """Container shell bilgilerini al"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        
        # Container'ın shell'ini bul
        shell_info = {
            'shell': '/bin/sh',  # Default
            'user': 'root',
            'working_dir': '/',
            'environment': container.attrs.get('Config', {}).get('Env', [])
        }
        
        # Config'den shell bilgilerini al
        config = container.attrs.get('Config', {})
        if 'User' in config:
            shell_info['user'] = config['User']
        if 'WorkingDir' in config:
            shell_info['working_dir'] = config['WorkingDir']
        
        # Environment'dan shell bul
        env_vars = config.get('Env', [])
        for env_var in env_vars:
            if env_var.startswith('SHELL='):
                shell_info['shell'] = env_var.split('=', 1)[1]
                break
        
        return {'success': True, 'shell_info': shell_info}
        
    except Exception as e:
        print(f"Shell info error: {e}")
        return {'success': False, 'message': str(e)}

def execute_interactive_command(container_id, command):
    """Interactive komut çalıştır"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        if container.status != 'running':
            return {'success': False, 'message': 'Container is not running'}
        
        # Interactive exec
        exec_result = container.exec_run(
            command,
            stdout=True,
            stderr=True,
            stdin=True,
            tty=True,
            detach=False
        )
        
        output = exec_result.output.decode('utf-8') if exec_result.output else ''
        
        return {
            'success': True,
            'output': output,
            'command': command
        }
        
    except Exception as e:
        print(f"Interactive command error: {e}")
        return {'success': False, 'message': str(e)}

def get_available_commands(container_id):
    """Container'da kullanılabilir komutları al"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        if container.status != 'running':
            return {'success': False, 'message': 'Container is not running'}
        
        # Temel komutları test et
        basic_commands = ['ls', 'pwd', 'whoami', 'ps', 'df', 'free', 'top']
        available_commands = []
        
        for cmd in basic_commands:
            try:
                exec_result = container.exec_run(f'which {cmd}', stdout=True, stderr=True)
                if exec_result.exit_code == 0:
                    available_commands.append(cmd)
            except:
                pass
        
        return {
            'success': True,
            'available_commands': available_commands,
            'total_count': len(available_commands)
        }
        
    except Exception as e:
        print(f"Available commands error: {e}")
        return {'success': False, 'message': str(e)}
