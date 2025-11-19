"""
Docker Stats Manager
Container istatistiklerini yönetir
"""

import docker
import json
import math
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

def get_container_stats(container_id):
    """Container istatistikleri"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        if container.status != 'running':
            return {'success': False, 'message': 'Container is not running'}
        
        # Stats al
        stats = container.stats(stream=False)
        
        # CPU hesaplama
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
        cpu_count = len(stats['cpu_stats']['cpu_usage'].get('percpu_usage', [1]))
        
        cpu_percent = 0.0
        if system_delta > 0 and cpu_delta > 0:
            cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0
        
        # Memory bilgileri
        memory_usage = stats['memory_stats']['usage']
        memory_limit = stats['memory_stats'].get('limit', 0)
        memory_percent = 0.0
        if memory_limit > 0:
            memory_percent = (memory_usage / memory_limit) * 100.0
        
        # Network bilgileri
        network_stats = stats['networks']
        network_io = {'rx': 0, 'tx': 0, 'total': 0}
        if network_stats:
            for net_name, net_data in network_stats.items():
                network_io['rx'] += net_data.get('rx_bytes', 0)
                network_io['tx'] += net_data.get('tx_bytes', 0)
            network_io['total'] = network_io['rx'] + network_io['tx']
        
        # Block I/O bilgileri
        block_stats = stats['blkio_stats']
        block_io = {'read': 0, 'write': 0, 'total': 0}
        if block_stats and 'io_service_bytes' in block_stats:
            for io_data in block_stats['io_service_bytes']:
                if io_data['op'] == 'Read':
                    block_io['read'] += io_data['value']
                elif io_data['op'] == 'Write':
                    block_io['write'] += io_data['value']
            block_io['total'] = block_io['read'] + block_io['write']
        
        # PIDs bilgisi
        pids = stats.get('pids_stats', {}).get('current', 0)
        
        return {
            'success': True,
            'stats': {
                'cpu_percent': f"{cpu_percent:.1f}",
                'memory_usage': memory_usage,
                'memory_limit': memory_limit,
                'memory_percent': f"{memory_percent:.1f}",
                'network_rx': network_io['rx'],
                'network_tx': network_io['tx'],
                'network_total': network_io['total'],
                'block_read': block_io['read'],
                'block_write': block_io['write'],
                'block_total': block_io['total'],
                'pids': pids,
                'timestamp': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        print(f"Stats error: {e}")
        return {'success': False, 'message': str(e)}

def get_container_processes(container_id):
    """Container process listesi"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        if container.status != 'running':
            return {'success': False, 'message': 'Container is not running'}
        
        # top komutu çalıştır
        exec_result = container.exec_run('ps aux', stdout=True, stderr=True)
        output = exec_result.output.decode('utf-8') if exec_result.output else ''
        
        if exec_result.exit_code != 0:
            return {'success': False, 'message': 'Processes not accessible'}
        
        processes = []
        lines = output.split('\n')[1:]  # Header'ı atla
        
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 11:
                    process = {
                        'user': parts[0],
                        'pid': parts[1],
                        'cpu': parts[2],
                        'memory': parts[3],
                        'vsz': parts[4],
                        'rss': parts[5],
                        'tty': parts[6],
                        'stat': parts[7],
                        'start': parts[8],
                        'time': parts[9],
                        'command': ' '.join(parts[10:])
                    }
                    processes.append(process)
        
        return {
            'success': True,
            'processes': processes,
            'total_count': len(processes)
        }
        
    except Exception as e:
        print(f"Processes error: {e}")
        return {'success': False, 'message': str(e)}

def get_container_health(container_id):
    """Container sağlık durumu"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        
        # Health check bilgileri
        health = container.attrs.get('State', {}).get('Health', {})
        
        health_status = {
            'status': health.get('Status', 'unknown'),
            'failing_streak': health.get('FailingStreak', 0),
            'last_check': health.get('Log', [{}])[-1] if health.get('Log') else {}
        }
        
        return {
            'success': True,
            'health': health_status
        }
        
    except Exception as e:
        print(f"Health error: {e}")
        return {'success': False, 'message': str(e)}

def format_bytes(bytes):
    """Bytes'ı human readable formata çevir"""
    if bytes == 0:
        return '0 B'
    k = 1024
    sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    i = int(math.floor(math.log(bytes) / math.log(k)))
    return f"{bytes / (k ** i):.1f} {sizes[i]}"

def get_real_time_stats(container_id, duration=60):
    """Gerçek zamanlı istatistikler"""
    try:
        client = get_docker_client()
        if not client:
            return {'success': False, 'message': 'Docker not available'}
        
        container = client.containers.get(container_id)
        if container.status != 'running':
            return {'success': False, 'message': 'Container is not running'}
        
        # Stream stats
        stats_generator = container.stats(stream=True)
        stats_data = []
        
        for i, stats in enumerate(stats_generator):
            if i >= duration:  # 60 saniye sonra dur
                break
            
            # CPU hesaplama
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
            cpu_count = len(stats['cpu_stats']['cpu_usage']['percpu_usage'])
            
            cpu_percent = 0.0
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0
            
            # Memory bilgileri
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats'].get('limit', 0)
            
            stats_data.append({
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': f"{cpu_percent:.1f}",
                'memory_usage': memory_usage,
                'memory_limit': memory_limit
            })
        
        return {
            'success': True,
            'real_time_stats': stats_data,
            'duration': duration
        }
        
    except Exception as e:
        print(f"Real time stats error: {e}")
        return {'success': False, 'message': str(e)}
