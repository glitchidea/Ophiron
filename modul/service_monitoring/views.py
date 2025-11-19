from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .service_manager import service_manager
from .models import ServiceLog, ServiceMonitoringSettings
from datetime import datetime
import logging
import os
import subprocess
import json

logger = logging.getLogger(__name__)

def log_service_operation(service_name, action, status, message, user='Anonymous', ip_address=None, details=None):
    """Log Service operations to database"""
    try:
        settings = ServiceMonitoringSettings.get_global_settings()
        if settings.logging_enabled:
            ServiceLog.objects.create(
                service_name=service_name,
                action=action,
                status=status,
                message=message,
                user=user,
                ip_address=ip_address,
                details=details or {}
            )
            logger.info(f"Service operation logged: {service_name} - {action} - {status}")
    except Exception as e:
        logger.error(f"Failed to log Service operation: {e}")

@login_required
def service_monitoring_view(request):
    """Service monitoring main page"""
    try:
        return render(request, 'modules/service_monitoring/index.html', {
            'page_title': 'Service Monitoring',
            'active_module': 'service_monitoring'
        })
    except Exception as e:
        logger.error(f"Error loading service monitoring page: {e}")
        return render(request, 'core/error.html', {'error': str(e)})

@login_required
def get_services_data(request):
    """Service list API endpoint"""
    try:
        from django.core.cache import cache
        
        # Try to get from cache first
        cached_services = cache.get('service_monitoring_services')
        if cached_services:
            services = cached_services
            logger.info("Using cached service data")
        else:
            # Fallback to direct service manager call
            services = service_manager.get_services()
            # Cache the result for future use
            cache.set('service_monitoring_services', services, timeout=300)
            logger.info("Using fresh service data and caching it")
        
        categories = sorted(list(set(service.get('category', 'Other') for service in services)))

        data = {
            "timestamp": datetime.now().isoformat(),
            "services": services,
            "categories": categories,
            "total_services": len(services),
            "cached": cached_services is not None
        }

        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Error getting service list: {e}")
        return JsonResponse({
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "services": [],
            "categories": [],
            "total_services": 0
        }, status=500)

@csrf_protect
@require_http_methods(["POST"])
@login_required
def control_service(request, action, service_name):
    """Service control API endpoint"""
    try:
        success, message = service_manager.control_service(service_name, action)
        
        # Log the operation
        log_service_operation(
            service_name=service_name,
            action=action,
            status='success' if success else 'error',
            message=message,
            user=request.user.username if request.user.is_authenticated else 'Anonymous',
            ip_address=request.META.get('REMOTE_ADDR'),
            details={'action': action, 'success': success}
        )
        
        return JsonResponse({"success": success, "message": message})
    except Exception as e:
        logger.error(f"Error during service control: {e}")
        
        # Log the error
        log_service_operation(
            service_name=service_name,
            action=action,
            status='error',
            message=f'Service control failed: {str(e)}',
            user=request.user.username if request.user.is_authenticated else 'Anonymous',
            ip_address=request.META.get('REMOTE_ADDR'),
            details={'action': action, 'error': str(e)}
        )
        
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@csrf_protect
@require_http_methods(["POST"])
@login_required
def delete_service(request, service_name):
    """Service deletion API endpoint"""
    try:
        success, message = service_manager.delete_service(service_name)
        return JsonResponse({"success": success, "message": message})
    except Exception as e:
        logger.error(f"Error during service deletion: {e}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def get_saved_services(request):
    """Get list of saved services."""
    try:
        services = []
        systemd_path = "/etc/systemd/system"

        if os.path.exists(systemd_path):
            for file in os.listdir(systemd_path):
                if file.endswith('.service'):
                    service_path = os.path.join(systemd_path, file)
                    service_name = file[:-8]  # Remove .service extension

                    # Get service status
                    try:
                        status = subprocess.run(
                            ['systemctl', 'is-active', service_name],
                            capture_output=True,
                            text=True
                        ).stdout.strip()
                    except:
                        status = 'unknown'

                    # Get creation time
                    try:
                        created_at = datetime.fromtimestamp(
                            os.path.getctime(service_path)
                        ).isoformat()
                    except:
                        created_at = None

                    services.append({
                        'id': service_name,
                        'name': service_name,
                        'status': status,
                        'created_at': created_at
                    })

        return JsonResponse({
            "success": True,
            "services": services
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e),
            "services": []
        }, status=500)

@csrf_protect
@require_http_methods(["DELETE"])
@login_required
def delete_saved_service(request, service_id):
    """Delete a saved service."""
    try:
        import os
        import subprocess

        service_path = f"/etc/systemd/system/{service_id}.service"

        if not os.path.exists(service_path):
            return JsonResponse({
                "success": False,
                "message": "Service not found."
            }, status=404)

        try:
            # Stop and disable the service
            subprocess.run(['systemctl', 'stop', service_id], check=True)
            subprocess.run(['systemctl', 'disable', service_id], check=True)

            # Delete the service file
            os.remove(service_path)

            # Reload systemd
            subprocess.run(['systemctl', 'daemon-reload'], check=True)

            return JsonResponse({
                "success": True,
                "message": f"{service_id} service successfully deleted."
            })

        except subprocess.CalledProcessError as e:
            return JsonResponse({
                "success": False,
                "message": f"Error deleting service: {str(e)}"
            }, status=500)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }, status=500)

@require_http_methods(["GET"])
@login_required
def get_service_logs(request, service_name):
    """Get service logs."""
    try:
        lines = request.GET.get('lines', 50)
        try:
            lines = int(lines)
        except ValueError:
            lines = 50

        logs = service_manager.get_service_logs(service_name, lines)
        return JsonResponse({
            "success": True,
            "logs": logs,
            "service_name": service_name
        })
    except Exception as e:
        logger.error(f"Error getting service logs: {e}")
        return JsonResponse({
            "success": False,
            "message": str(e),
            "logs": []
        }, status=500)

@require_http_methods(["GET"])
@login_required
def get_service_details(request, service_name):
    """Get detailed service information."""
    try:
        details = service_manager.get_service_details(service_name)
        return JsonResponse({
            "success": True,
            "details": details
        })
    except Exception as e:
        logger.error(f"Error getting service details: {e}")
        return JsonResponse({
            "success": False,
            "message": str(e),
            "details": {}
        }, status=500)


@require_http_methods(["GET"])
@login_required
def get_live_mode_status(request):
    """Get Service Monitoring live mode status"""
    try:
        from django.core.cache import cache
        from datetime import datetime
        
        # Check cache for last update
        last_update = cache.get('service_monitoring_last_update')
        services_count = len(cache.get('service_monitoring_services', []))
        
        # Get settings from database
        settings = ServiceMonitoringSettings.get_global_settings()
        
        return JsonResponse({
            "success": True,
            "live_mode_enabled": settings.live_mode_enabled,
            "interval": settings.monitoring_interval,
            "status": "active" if settings.live_mode_enabled else "inactive",
            "last_update": last_update,
            "cached_services": services_count
        })
    except Exception as e:
        logger.error(f"Error getting live mode status: {e}")
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)

@csrf_protect
@require_http_methods(["POST"])
@login_required
def toggle_live_mode(request):
    """Toggle Service Monitoring live mode"""
    try:
        import json
        
        data = json.loads(request.body)
        live_mode = data.get('live_mode', False)
        interval = data.get('interval', 2.0)
        
        # Update settings in database
        settings = ServiceMonitoringSettings.get_global_settings()
        settings.live_mode_enabled = live_mode
        settings.monitoring_interval = float(interval)
        settings.last_modified_by = request.user.username
        settings.save()
        
        # Update cache
        from django.core.cache import cache
        cache.set('service_monitoring_live_mode_enabled', live_mode, timeout=None)
        cache.set('service_monitoring_live_mode_interval', float(interval), timeout=None)
        
        logger.info(f"Service Monitoring live mode toggled: {live_mode}, interval: {interval}")
        
        return JsonResponse({
            "success": True,
            "message": f"Live mode {'enabled' if live_mode else 'disabled'}",
            "live_mode_enabled": live_mode,
            "interval": float(interval)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Invalid JSON data"
        }, status=400)
    except Exception as e:
        logger.error(f"Error toggling live mode: {e}")
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)

@csrf_protect
@require_http_methods(["POST"])
@login_required
def force_refresh(request):
    """Force refresh Service Monitoring cache"""
    try:
        from .tasks import force_refresh_services
        
        # Trigger background task
        task = force_refresh_services.delay()
        
        return JsonResponse({
            "success": True,
            "message": "Service Monitoring cache refresh initiated",
            "task_id": task.id
        })
        
    except Exception as e:
        logger.error(f"Error force refreshing Service Monitoring: {e}")
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)


# ===== LOGGING API ENDPOINTS =====

@require_http_methods(["GET"])
@login_required
def get_logging_status(request):
    """Get Service Monitoring logging status"""
    try:
        settings = ServiceMonitoringSettings.get_global_settings()
        return JsonResponse({
            'success': True,
            'logging_enabled': settings.logging_enabled,
            'log_retention_days': settings.log_retention_days,
            'realtime_logging': settings.realtime_logging,
            'last_modified_by': settings.last_modified_by or 'N/A'
        })
    except Exception as e:
        logger.error(f"Error getting Service Monitoring logging status: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["POST"])
@login_required
def toggle_logging(request):
    """Toggle Service Monitoring logging"""
    try:
        data = json.loads(request.body)
        settings = ServiceMonitoringSettings.get_global_settings()
        
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
        log_service_operation(
            service_name='Service Monitoring',
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
        logger.error(f"Error toggling Service Monitoring logging: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)