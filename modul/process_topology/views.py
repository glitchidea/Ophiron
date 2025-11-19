from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext as _
import json
import psutil
import os
from collections import defaultdict


def index(request):
    """Main process topology page"""
    context = {
        'page_title': _('Process Topology'),
        'active_module': 'process_topology',
    }
    return render(request, 'modules/process_topology/index.html', context)


def get_topology_data(request):
    """API endpoint to get process topology data"""
    try:
        # Get all running processes
        processes = []
        process_connections = defaultdict(list)
        
        for proc in psutil.process_iter(['pid', 'name', 'ppid', 'status', 'cpu_percent', 'memory_percent', 'username']):
            try:
                proc_info = proc.info
                processes.append({
                    'id': str(proc_info['pid']),
                    'name': proc_info['name'],
                    'ppid': str(proc_info['ppid']) if proc_info['ppid'] else None,
                    'status': proc_info['status'],
                    'cpu_percent': proc_info['cpu_percent'] or 0,
                    'memory_percent': proc_info['memory_percent'] or 0,
                    'username': proc_info['username'] or 'unknown'
                })
                
                # Create parent-child relationships
                if proc_info['ppid']:
                    process_connections[str(proc_info['ppid'])].append(str(proc_info['pid']))
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Create nodes
        nodes = []
        for proc in processes:
            # Determine process type based on status
            type_mapping = {
                'running': 0,
                'sleeping': 1,
                'stopped': 2,
                'zombie': 3,
                'disk-sleep': 4,
                'dead': 5,
                'waking': 6,
                'parked': 7
            }
            
            proc_type = type_mapping.get(proc['status'], 0)
            
            # Calculate size based on memory usage
            size = max(5, min(50, proc['memory_percent'] * 2))
            
            nodes.append({
                'id': proc['id'],
                'name': proc['name'],
                'type': proc_type,
                'size': size,
                'status': proc['status'],
                'cpu_percent': proc['cpu_percent'],
                'memory_percent': proc['memory_percent'],
                'username': proc['username']
            })
        
        # Create links (parent-child relationships)
        links = []
        for parent_pid, child_pids in process_connections.items():
            for child_pid in child_pids:
                links.append({
                    'source': parent_pid,
                    'target': child_pid,
                    'type': 'parent-child'
                })
        
        # Add system node as root
        system_node = {
            'id': '0',
            'name': 'System',
            'type': -1,
            'size': 30,
            'status': 'system',
            'cpu_percent': 0,
            'memory_percent': 0,
            'username': 'system'
        }
        nodes.insert(0, system_node)
        
        # Connect system to main processes
        main_processes = [node for node in nodes[1:] if not any(link['target'] == node['id'] for link in links)]
        for proc in main_processes[:10]:  # Limit to first 10 main processes
            links.append({
                'source': '0',
                'target': proc['id'],
                'type': 'system'
            })
        
        data = {
            'nodes': nodes,
            'links': links,
            'status': 'success',
            'total_processes': len(processes)
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'nodes': [],
            'links': [],
            'status': 'error',
            'message': f'Error getting process data: {str(e)}'
        })


@csrf_exempt
def refresh_topology(request):
    """API endpoint to refresh process topology data"""
    if request.method == 'POST':
        # Placeholder for refresh logic
        return JsonResponse({'status': 'success', 'message': 'Topology refreshed'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
