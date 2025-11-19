"""
SMTP Views
API endpoints for SMTP configuration and email automation
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.mail import get_connection
from django.core.mail.backends.smtp import EmailBackend
from .models import SMTPConfig, EmailAutomation, EmailLog
from .automations.cve_email import CVEEmailAutomation
from .utils import encrypt_password, decrypt_password

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def get_smtp_config(request):
    """Get current SMTP configuration"""
    try:
        config = SMTPConfig.objects.first()
        
        if not config:
            return JsonResponse({
                'success': True,
                'config': None
            })
        
        # Don't send password in response (security)
        return JsonResponse({
            'success': True,
            'config': {
                'id': config.id,
                'host': config.host,
                'port': config.port,
                'use_tls': config.use_tls,
                'use_ssl': config.use_ssl,
                'username': config.username,
                'from_email': config.from_email or config.username,  # Fallback to username
                'from_name': config.from_name,
                'is_active': config.is_active,
                'last_test_success': config.last_test_success,
                'last_test_at': config.last_test_at.isoformat() if config.last_test_at else None,
                'last_test_error': config.last_test_error,
                'last_modified_at': config.last_modified_at.isoformat(),
                'has_password': bool(config.password),  # Indicate if password is set (not the actual password)
            }
        })
    except Exception as e:
        logger.error(f"Error getting SMTP config: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def save_smtp_config(request):
    """Save or update SMTP configuration"""
    try:
        data = json.loads(request.body)
        
        # Validation
        host = data.get('host', '').strip()
        username = data.get('username', '').strip()
        
        if not host:
            return JsonResponse({
                'success': False,
                'error': 'SMTP host is required'
            }, status=400)
        
        if not username:
            return JsonResponse({
                'success': False,
                'error': 'Email address is required'
            }, status=400)
        
        # Email validation
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, username):
            return JsonResponse({
                'success': False,
                'error': 'Invalid email address format'
            }, status=400)
        
        config, created = SMTPConfig.objects.get_or_create(pk=1)  # Single config
        
        # Update fields
        config.host = host
        config.port = int(data.get('port', config.port or 587))
        config.use_tls = data.get('use_tls', config.use_tls if not created else True)
        config.use_ssl = data.get('use_ssl', config.use_ssl if not created else False)
        config.username = username
        
        # Only update password if provided (not empty)
        password = data.get('password', '').strip()
        if password:
            # Encrypt password using user-specific key
            config.password = encrypt_password(password, request.user)
        # If password not provided and config is new, return error
        elif created and not password:
            return JsonResponse({
                'success': False,
                'error': 'Password is required for new configuration'
            }, status=400)
        
        # From email is automatically set to username (sender email)
        from_email = data.get('from_email', username)
        if not from_email:
            from_email = username
        config.from_email = from_email
        
        config.from_name = data.get('from_name', 'Ophiron System')
        config.is_active = data.get('is_active', config.is_active if not created else False)
        config.last_modified_by = request.user
        
        config.save()
        
        return JsonResponse({
            'success': True,
            'message': 'SMTP configuration saved successfully',
            'created': created
        })
        
    except ValueError as e:
        logger.error(f"Validation error saving SMTP config: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Invalid input: {str(e)}'
        }, status=400)
    except Exception as e:
        logger.error(f"Error saving SMTP config: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def test_smtp_connection(request):
    """Test SMTP connection"""
    try:
        data = json.loads(request.body)
        
        # Get test parameters from request or use saved config
        host = data.get('host')
        port = data.get('port')
        use_tls = data.get('use_tls')
        use_ssl = data.get('use_ssl')
        username = data.get('username')
        password = data.get('password')
        
        # Get saved config if exists
        saved_config = SMTPConfig.objects.first()
        
        # Use saved config values if not provided in request
        if not host and saved_config:
            host = saved_config.host
        if port is None and saved_config:
            port = saved_config.port
        if use_tls is None and saved_config:
            use_tls = saved_config.use_tls
        if use_ssl is None and saved_config:
            use_ssl = saved_config.use_ssl
        if not username and saved_config:
            username = saved_config.username
        if not password and saved_config:
            # Try to decrypt saved password
            if saved_config.password:
                try:
                    password = decrypt_password(saved_config.password, request.user)
                except Exception as e:
                    logger.warning(f"Could not decrypt saved password: {e}")
                    password = saved_config.password  # Fallback to raw (might be unencrypted)
        
        # Validation
        if not host:
            return JsonResponse({
                'success': False,
                'error': 'SMTP host is required. Please configure SMTP settings first.'
            }, status=400)
        
        if not username:
            return JsonResponse({
                'success': False,
                'error': 'Email address is required. Please configure SMTP settings first.'
            }, status=400)
        
        # If password not provided, try to decrypt saved password
        if not password and saved_config and saved_config.password:
            try:
                password = decrypt_password(saved_config.password, request.user)
            except Exception as e:
                logger.error(f"Error decrypting saved password: {e}")
                password = None
        
        if not password:
            return JsonResponse({
                'success': False,
                'error': 'Password is required. Please enter password or save SMTP configuration first.'
            }, status=400)
        
        # Convert port to int
        port = int(port) if port else 587
        use_tls = use_tls if use_tls is not None else True
        use_ssl = use_ssl if use_ssl is not None else False
        
        try:
            connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=host,
                port=port,
                username=username,
                password=password,
                use_tls=use_tls,
                use_ssl=use_ssl,
            )
            
            # Test connection
            connection.open()
            connection.close()
            
            # Update config if exists
            if saved_config:
                saved_config.last_test_success = True
                saved_config.last_test_at = timezone.now()
                saved_config.last_test_error = None
                saved_config.save()
            
            return JsonResponse({
                'success': True,
                'message': 'SMTP connection test successful'
            })
            
        except Exception as e:
            # Update config with error
            if saved_config:
                saved_config.last_test_success = False
                saved_config.last_test_at = timezone.now()
                saved_config.last_test_error = str(e)
                saved_config.save()
            
            return JsonResponse({
                'success': False,
                'error': f'Connection failed: {str(e)}'
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error testing SMTP connection: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_automations(request):
    """Get all email automations"""
    try:
        automations = EmailAutomation.objects.all().order_by('-created_at')
        
        automations_data = []
        for automation in automations:
            automations_data.append({
                'id': automation.id,
                'name': automation.name,
                'automation_type': automation.automation_type,
                'is_enabled': automation.is_enabled,
                'schedule_type': automation.schedule_type,
                'schedule_time': automation.schedule_time.strftime('%H:%M') if automation.schedule_time else None,
                'schedule_days': automation.schedule_days,
                'schedule_cron': automation.schedule_cron,
                'recipients': automation.recipients,
                'config': automation.config,
                'last_run_at': automation.last_run_at.isoformat() if automation.last_run_at else None,
                'last_run_status': automation.last_run_status,
                'next_run_at': automation.next_run_at.isoformat() if automation.next_run_at else None,
                'created_at': automation.created_at.isoformat(),
                'schedule_description': automation.get_schedule_description(),
            })
        
        return JsonResponse({
            'success': True,
            'automations': automations_data
        })
        
    except Exception as e:
        logger.error(f"Error getting automations: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_automation(request, automation_id):
    """Get single automation"""
    try:
        automation = EmailAutomation.objects.get(pk=automation_id)
        
        return JsonResponse({
            'success': True,
            'automation': {
                'id': automation.id,
                'name': automation.name,
                'automation_type': automation.automation_type,
                'is_enabled': automation.is_enabled,
                'schedule_type': automation.schedule_type,
                'schedule_time': automation.schedule_time.strftime('%H:%M') if automation.schedule_time else None,
                'schedule_days': automation.schedule_days,
                'schedule_cron': automation.schedule_cron,
                'recipients': automation.recipients,
                'config': automation.config,
                'last_run_at': automation.last_run_at.isoformat() if automation.last_run_at else None,
                'last_run_status': automation.last_run_status,
                'next_run_at': automation.next_run_at.isoformat() if automation.next_run_at else None,
            }
        })
        
    except EmailAutomation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Automation not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting automation: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def save_automation(request):
    """Save or update email automation"""
    try:
        data = json.loads(request.body)
        
        automation_id = data.get('id')
        
        if automation_id:
            automation = EmailAutomation.objects.get(pk=automation_id)
        else:
            automation = EmailAutomation()
            automation.created_by = request.user
        
        # If automation exists but no created_by, set it
        if automation and not automation.created_by:
            automation.created_by = request.user
        
        automation.name = data.get('name', automation.name)
        automation.automation_type = data.get('automation_type', automation.automation_type)
        automation.is_enabled = data.get('is_enabled', automation.is_enabled)
        automation.schedule_type = data.get('schedule_type', automation.schedule_type)
        
        # Parse schedule_time
        schedule_time_str = data.get('schedule_time')
        if schedule_time_str:
            from datetime import datetime
            try:
                automation.schedule_time = datetime.strptime(schedule_time_str, '%H:%M').time()
            except:
                pass
        
        automation.schedule_days = data.get('schedule_days', automation.schedule_days)
        automation.schedule_cron = data.get('schedule_cron', automation.schedule_cron)
        # Recipients are now automatic - keep empty array
        automation.recipients = []  # Will be set automatically from user's email
        automation.config = data.get('config', automation.config or {})
        automation.last_modified_by = request.user
        
        automation.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Automation saved successfully',
            'automation_id': automation.id
        })
        
    except Exception as e:
        logger.error(f"Error saving automation: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def delete_automation(request, automation_id):
    """Delete email automation"""
    try:
        automation = EmailAutomation.objects.get(pk=automation_id)
        automation.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Automation deleted successfully'
        })
        
    except EmailAutomation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Automation not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error deleting automation: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def run_automation(request, automation_id):
    """Manually trigger an automation"""
    try:
        automation = EmailAutomation.objects.get(pk=automation_id)
        
        if automation.automation_type == 'cve':
            handler = CVEEmailAutomation(automation)
            result = handler.run()
            
            return JsonResponse({
                'success': result['success'],
                'message': result['message'],
                'cves_found': result.get('cves_found', 0),
                'emails_sent': result.get('emails_sent', 0)
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'Automation type {automation.automation_type} not yet implemented'
            }, status=400)
        
    except EmailAutomation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Automation not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error running automation: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_email_logs(request):
    """Get email logs"""
    try:
        automation_id = request.GET.get('automation_id')
        limit = int(request.GET.get('limit', 50))
        
        logs = EmailLog.objects.all()
        
        if automation_id:
            logs = logs.filter(automation_id=automation_id)
        
        logs = logs.order_by('-created_at')[:limit]
        
        logs_data = []
        for log in logs:
            logs_data.append({
                'id': log.id,
                'automation': log.automation.name if log.automation else None,
                'recipient': log.recipient,
                'subject': log.subject,
                'status': log.status,
                'error_message': log.error_message,
                'sent_at': log.sent_at.isoformat() if log.sent_at else None,
                'created_at': log.created_at.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'logs': logs_data
        })
        
    except Exception as e:
        logger.error(f"Error getting email logs: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

