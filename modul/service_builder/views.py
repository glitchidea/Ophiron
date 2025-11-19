from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils.translation import gettext as _
import json
import os
import subprocess
import socket
import psutil
import pwd
import grp
import logging
from pathlib import Path
from .models import ServiceTemplate, ServiceLog, ServiceConfiguration
from .utils import (
    validate_application_path, 
    check_port_availability, 
    suggest_service_config,
    analyze_python_file,
    create_systemd_service,
    update_systemd_service,
    delete_systemd_service,
    get_system_users,
    get_network_interfaces,
    log_service_operation,
    ServiceManager,
    detect_service_manager,
    get_primary_service_manager
)

logger = logging.getLogger(__name__)


@login_required
def index(request):
    """Service Builder main page"""
    try:
        # Get recent service configurations
        recent_services = ServiceConfiguration.objects.filter(is_active=True).order_by('-created_at')[:5]
        
        # Get service templates
        templates = ServiceTemplate.objects.filter(is_active=True).order_by('-created_at')[:5]
        
        # Get recent logs
        recent_logs = ServiceLog.objects.all().order_by('-created_at')[:10]
        
        context = {
            'page_title': _('Service Builder'),
            'active_module': 'service_builder',
            'recent_services': recent_services,
            'templates': templates,
            'recent_logs': recent_logs,
        }
        
        return render(request, 'modules/service_builder/index.html', context)
        
    except Exception as e:
        logger.error(f"Error loading service builder page: {e}")
        messages.error(request, f"Error loading page: {str(e)}")
        return render(request, 'core/error.html', {'error': str(e)})


@login_required
def create_service(request):
    """Service creation page"""
    try:
        # Get system users for dropdown
        system_users = get_system_users()
        
        # Get network interfaces
        network_interfaces = get_network_interfaces()
        
        # Get service templates
        templates = ServiceTemplate.objects.filter(is_active=True)
        
        context = {
            'page_title': _('Create Service'),
            'active_module': 'service_builder',
            'system_users': system_users,
            'network_interfaces': network_interfaces,
            'templates': templates,
        }
        
        return render(request, 'modules/service_builder/create_service.html', context)
        
    except Exception as e:
        logger.error(f"Error loading create service page: {e}")
        messages.error(request, f"Error loading page: {str(e)}")
        return render(request, 'core/error.html', {'error': str(e)})


@login_required
def templates(request):
    """Service templates page"""
    try:
        templates = ServiceTemplate.objects.all().order_by('-created_at')
        
        context = {
            'page_title': _('Service Templates'),
            'active_module': 'service_builder',
            'templates': templates,
        }
        
        return render(request, 'modules/service_builder/templates.html', context)
        
    except Exception as e:
        logger.error(f"Error loading templates page: {e}")
        messages.error(request, f"Error loading page: {str(e)}")
        return render(request, 'core/error.html', {'error': str(e)})


@login_required
def services(request):
    """Services management page"""
    try:
        services = ServiceConfiguration.objects.all().order_by('-created_at')
        
        context = {
            'page_title': _('Services'),
            'active_module': 'service_builder',
            'services': services,
        }
        
        return render(request, 'modules/service_builder/services.html', context)
        
    except Exception as e:
        logger.error(f"Error loading services page: {e}")
        messages.error(request, f"Error loading page: {str(e)}")
        return render(request, 'core/error.html', {'error': str(e)})


@login_required
def logs(request):
    """Service logs page"""
    try:
        logs = ServiceLog.objects.all().order_by('-created_at')
        
        context = {
            'page_title': _('Service Logs'),
            'active_module': 'service_builder',
            'logs': logs,
        }
        
        return render(request, 'modules/service_builder/logs.html', context)
        
    except Exception as e:
        logger.error(f"Error loading logs page: {e}")
        messages.error(request, f"Error loading page: {str(e)}")
        return render(request, 'core/error.html', {'error': str(e)})


@login_required
def service_detail(request, service_name):
    """Service detail page"""
    try:
        service = get_object_or_404(ServiceConfiguration, name=service_name)
        
        # Get service status
        status_result = get_service_status(service_name)
        
        # Get recent logs for this service
        service_logs = ServiceLog.objects.filter(service_name=service_name).order_by('-created_at')[:20]
        
        context = {
            'page_title': _('Service: %(service_name)s') % {'service_name': service_name},
            'active_module': 'service_builder',
            'service': service,
            'service_status': status_result,
            'service_logs': service_logs,
        }
        
        return render(request, 'modules/service_builder/service_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error loading service detail page: {e}")
        messages.error(request, f"Error loading service: {str(e)}")
        return redirect('service_builder:services')


@login_required
def edit_service(request, service_name):
    """Edit service page"""
    try:
        service = get_object_or_404(ServiceConfiguration, name=service_name)
        
        # Get system users for dropdown
        system_users = get_system_users()
        
        # Get network interfaces
        network_interfaces = get_network_interfaces()
        
        context = {
            'page_title': _('Edit Service: %(service_name)s') % {'service_name': service_name},
            'active_module': 'service_builder',
            'service': service,
            'system_users': system_users,
            'network_interfaces': network_interfaces,
        }
        
        return render(request, 'modules/service_builder/edit_service.html', context)
        
    except Exception as e:
        logger.error(f"Error loading edit service page: {e}")
        messages.error(request, f"Error loading edit page: {str(e)}")
        return redirect('service_builder:services')


@login_required
def service_control(request, service_name, action):
    """Service control actions"""
    try:
        service = get_object_or_404(ServiceConfiguration, name=service_name)
        
        # Perform service control action
        success, message = control_service(service_name, action)
        
        if success:
            messages.success(request, f"Service {action} successful: {message}")
            log_service_operation(service_name, action, 'success', message, request.user.username, request.META.get('REMOTE_ADDR'))
        else:
            messages.error(request, f"Service {action} failed: {message}")
            log_service_operation(service_name, action, 'error', message, request.user.username, request.META.get('REMOTE_ADDR'))
        
        return redirect('service_builder:service_detail', service_name=service_name)
        
    except Exception as e:
        logger.error(f"Error controlling service: {e}")
        messages.error(request, f"Error controlling service: {str(e)}")
        return redirect('service_builder:services')


# API Endpoints

@csrf_exempt
@require_http_methods(["POST"])
def api_validate_path(request):
    """Validate application path"""
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            return JsonResponse({'success': False, 'error': f'Invalid JSON data: {str(e)}'})
        
        app_path = data.get('app_path', '')
        app_type = data.get('app_type', 'normal')
        
        if not app_path:
            return JsonResponse({'success': False, 'error': 'Application path is required'})
        
        is_valid, message, final_path = validate_application_path(app_path, app_type)
        
        return JsonResponse({
            'success': True,
            'valid': is_valid,
            'message': message,
            'final_path': final_path
        })
        
    except Exception as e:
        logger.error(f"Error validating path: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(["GET"])
def api_check_port(request, port):
    """Check if port is available"""
    try:
        is_available = check_port_availability(port)
        return JsonResponse({'success': True, 'available': is_available})
        
    except Exception as e:
        logger.error(f"Error checking port: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def api_suggest_config(request):
    """Suggest service configuration"""
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            return JsonResponse({'success': False, 'error': f'Invalid JSON data: {str(e)}'})
        
        app_path = data.get('app_path', '')
        app_type = data.get('app_type', 'normal')
        
        if not app_path:
            return JsonResponse({'success': False, 'error': 'Application path is required'})
        
        suggestions = suggest_service_config(app_path, app_type)
        return JsonResponse({'success': True, **suggestions})
        
    except Exception as e:
        logger.error(f"Error suggesting config: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def api_analyze_python(request):
    """Analyze Python file for configuration"""
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            return JsonResponse({'success': False, 'error': f'Invalid JSON data: {str(e)}'})
        
        file_path = data.get('file_path', '')
        
        if not file_path or not file_path.endswith('.py'):
            return JsonResponse({'success': False, 'error': 'Valid Python file path is required'})
        
        analysis = analyze_python_file(file_path)
        return JsonResponse({'success': True, **analysis})
        
    except Exception as e:
        logger.error(f"Error analyzing Python file: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def api_create_service(request):
    """Create new service"""
    try:
        # Parse JSON data safely
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            return JsonResponse({'success': False, 'error': f'Invalid JSON data: {str(e)}'})
        
        # Validate required fields
        required_fields = ['name', 'application_path', 'user']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'error': f'{field} is required'})
        
        # Create service configuration
        service_config = ServiceConfiguration.objects.create(
            name=data['name'],
            description=data.get('description', ''),
            service_type=data.get('service_type', 'normal'),
            application_path=data['application_path'],
            interpreter=data.get('interpreter', ''),
            user=data['user'],
            working_directory=data.get('working_directory', ''),
            port=data.get('port'),
            host=data.get('host', '0.0.0.0'),
            restart_policy=data.get('restart_policy', 'always'),
            environment_vars=data.get('environment_vars', ''),
        )
        
        # Create systemd service
        success, message = create_systemd_service(service_config)
        
        if success:
            log_service_operation(service_config.name, 'create', 'success', message, request.user.username, request.META.get('REMOTE_ADDR'))
            return JsonResponse({
                'success': True, 
                'message': message, 
                'service_id': service_config.id,
                'service_name': service_config.name
            })
        else:
            service_config.delete()
            log_service_operation(service_config.name, 'create', 'error', message, request.user.username, request.META.get('REMOTE_ADDR'))
            return JsonResponse({'success': False, 'error': message})
        
    except Exception as e:
        logger.error(f"Error creating service: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(["GET"])
def api_service_status(request, service_name):
    """Get service status"""
    try:
        status_result = get_service_status(service_name)
        return JsonResponse({'success': True, **status_result})
        
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(["GET"])
def api_service_logs(request, service_name):
    """Get service logs"""
    try:
        logs = ServiceLog.objects.filter(service_name=service_name).order_by('-created_at')[:50]
        logs_data = []
        for log in logs:
            logs_data.append({
                'action': log.action,
                'status': log.status,
                'message': log.message,
                'user': log.user,
                'created_at': log.created_at.isoformat(),
                'details': log.details
            })
        
        return JsonResponse({'success': True, 'logs': logs_data})
        
    except Exception as e:
        logger.error(f"Error getting service logs: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(["GET"])
def api_system_users(request):
    """Get system users"""
    try:
        users = get_system_users()
        return JsonResponse({'success': True, 'users': users})
        
    except Exception as e:
        logger.error(f"Error getting system users: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(["GET"])
def api_network_interfaces(request):
    """Get network interfaces"""
    try:
        interfaces = get_network_interfaces()
        return JsonResponse({'success': True, 'interfaces': interfaces})
        
    except Exception as e:
        logger.error(f"Error getting network interfaces: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_service_managers(request):
    """Get available service managers"""
    try:
        managers = detect_service_manager()
        primary = get_primary_service_manager()
        return JsonResponse({
            'success': True,
            'managers': managers,
            'primary': primary
        })
    except Exception as e:
        logger.error(f"Error getting service managers: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_http_methods(["PUT"])
def api_update_service(request, service_name):
    """Update service configuration"""
    try:
        # Parse JSON data safely
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            return JsonResponse({'success': False, 'error': f'Invalid JSON data: {str(e)}'})
        
        # Get service configuration
        try:
            service_config = ServiceConfiguration.objects.get(name=service_name)
        except ServiceConfiguration.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Service not found'})
        
        # Update service configuration
        service_config.description = data.get('description', service_config.description)
        service_config.service_type = data.get('service_type', service_config.service_type)
        service_config.application_path = data.get('application_path', service_config.application_path)
        service_config.interpreter = data.get('interpreter', service_config.interpreter)
        service_config.user = data.get('user', service_config.user)
        service_config.working_directory = data.get('working_directory', service_config.working_directory)
        service_config.port = data.get('port', service_config.port)
        service_config.host = data.get('host', service_config.host)
        service_config.restart_policy = data.get('restart_policy', service_config.restart_policy)
        service_config.environment_vars = data.get('environment_vars', service_config.environment_vars)
        
        # Save changes
        service_config.save()
        
        # Update systemd service
        success, message = update_systemd_service(service_config)
        
        if success:
            log_service_operation(service_name, 'update', 'success', message, request.user.username, request.META.get('REMOTE_ADDR'))
            return JsonResponse({'success': True, 'message': message, 'service_id': service_config.id})
        else:
            log_service_operation(service_name, 'update', 'error', message, request.user.username, request.META.get('REMOTE_ADDR'))
            return JsonResponse({'success': False, 'error': message})
        
    except Exception as e:
        logger.error(f"Error updating service: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def api_service_control(request, service_name, action):
    """Control service via API"""
    try:
        # Get service configuration
        try:
            service_config = ServiceConfiguration.objects.get(name=service_name)
        except ServiceConfiguration.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Service not found'})
        
        # Control service
        success, message = control_service(service_name, action)
        
        if success:
            log_service_operation(service_name, action, 'success', message, request.user.username, request.META.get('REMOTE_ADDR'))
            return JsonResponse({'success': True, 'message': message})
        else:
            log_service_operation(service_name, action, 'error', message, request.user.username, request.META.get('REMOTE_ADDR'))
            return JsonResponse({'success': False, 'error': message})
        
    except Exception as e:
        logger.error(f"Error controlling service: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["DELETE"])
def api_delete_service(request, service_name):
    """Delete service completely"""
    try:
        # Get service configuration
        try:
            service_config = ServiceConfiguration.objects.get(name=service_name)
        except ServiceConfiguration.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Service not found'})
        
        # Delete systemd service
        success, message = delete_systemd_service(service_name)
        
        if success:
            # Delete from database
            service_config.delete()
            log_service_operation(service_name, 'delete', 'success', message, request.user.username, request.META.get('REMOTE_ADDR'))
            return JsonResponse({'success': True, 'message': message})
        else:
            log_service_operation(service_name, 'delete', 'error', message, request.user.username, request.META.get('REMOTE_ADDR'))
            return JsonResponse({'success': False, 'error': message})
        
    except Exception as e:
        logger.error(f"Error deleting service: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


# Helper functions

def get_service_status(service_name):
    """Get service status from systemd"""
    try:
        result = subprocess.run(
            ['sudo', 'systemctl', 'status', f'{service_name}.service'],
            capture_output=True,
            text=True
        )
        
        if 'Active: active (running)' in result.stdout:
            return {'status': 'running', 'message': 'Service is running'}
        elif 'Active: inactive (dead)' in result.stdout:
            return {'status': 'stopped', 'message': 'Service is stopped'}
        else:
            return {'status': 'unknown', 'message': result.stdout}
            
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def control_service(service_name, action):
    """Control service (start, stop, restart, enable, disable)"""
    try:
        if action in ['start', 'stop', 'restart', 'enable', 'disable']:
            result = subprocess.run(
                ['sudo', 'systemctl', action, f'{service_name}.service'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, f"Service {action} successful"
            else:
                return False, f"Service {action} failed: {result.stderr}"
        else:
            return False, f"Invalid action: {action}"
            
    except Exception as e:
        return False, f"Error controlling service: {str(e)}"