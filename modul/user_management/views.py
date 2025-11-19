from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.utils.translation import gettext as _
import json
import subprocess
import pwd
import grp
import os
from datetime import datetime, timedelta
from .models import SystemUser, UserActivity, UserPermission, UserSession, SystemInfo


@login_required
def user_management_index(request):
    """Main user management page"""
    try:
        # Update system info
        SystemInfo.update_system_info()
        
        # Get system users
        system_users = SystemUser.objects.all().order_by('uid')
        
        # Get recent activities
        recent_activities = UserActivity.objects.select_related('user').order_by('-timestamp')[:10]
        
        # Get active sessions
        active_sessions = UserSession.objects.filter(is_active=True).select_related('user').order_by('-last_activity')
        
        # Get system info
        system_info = SystemInfo.objects.first()
        
        context = {
            'page_title': _('User Management'),
            'system_users': system_users,
            'recent_activities': recent_activities,
            'active_sessions': active_sessions,
            'system_info': system_info,
        }
        
        return render(request, 'modules/user_management/index.html', context)
        
    except Exception as e:
        return render(request, 'modules/user_management/index.html', {
            'page_title': _('User Management'),
            'error': f'Error loading user management: {str(e)}'
        })


@login_required
@require_http_methods(["GET"])
def api_system_users(request):
    """API endpoint to get system users"""
    try:
        users = SystemUser.objects.all().order_by('uid')
        
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'uid': user.uid,
                'gid': user.gid,
                'home_directory': user.home_directory,
                'shell': user.shell,
                'is_system_user': user.is_system_user,
                'is_active': user.is_active,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'group_name': user.get_group_name(),
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'users': users_data,
            'total': len(users_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["GET"])
def api_user_details(request, user_id):
    """API endpoint to get detailed user information"""
    try:
        user = get_object_or_404(SystemUser, id=user_id)
        
        # Get user activities
        activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:20]
        
        # Get user permissions
        permissions = UserPermission.objects.filter(user=user)
        
        # Get user sessions
        sessions = UserSession.objects.filter(user=user).order_by('-last_activity')
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'uid': user.uid,
            'gid': user.gid,
            'home_directory': user.home_directory,
            'shell': user.shell,
            'is_system_user': user.is_system_user,
            'is_active': user.is_active,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'group_name': user.get_group_name(),
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat(),
            'activities': [
                {
                    'activity_type': activity.activity_type,
                    'description': activity.description,
                    'ip_address': activity.ip_address,
                    'timestamp': activity.timestamp.isoformat(),
                    'metadata': activity.metadata
                } for activity in activities
            ],
            'permissions': [
                {
                    'permission_name': perm.permission_name,
                    'permission_value': perm.permission_value,
                    'description': perm.description
                } for perm in permissions
            ],
            'sessions': [
                {
                    'session_id': session.session_id,
                    'ip_address': session.ip_address,
                    'user_agent': session.user_agent,
                    'login_time': session.login_time.isoformat(),
                    'last_activity': session.last_activity.isoformat(),
                    'is_active': session.is_active
                } for session in sessions
            ]
        }
        
        return JsonResponse({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_sync_users(request):
    """API endpoint to sync system users"""
    try:
        # Sync system users from /etc/passwd
        success = SystemUser.sync_system_users()
        
        if success:
            # Update system info
            SystemInfo.update_system_info()
            
            return JsonResponse({
                'success': True,
                'message': 'System users synchronized successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to synchronize system users'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["GET"])
def api_user_activities(request):
    """API endpoint to get user activities"""
    try:
        # Get query parameters
        user_id = request.GET.get('user_id')
        limit = int(request.GET.get('limit', 50))
        activity_type = request.GET.get('activity_type')
        
        # Build query
        activities_query = UserActivity.objects.select_related('user')
        
        if user_id:
            activities_query = activities_query.filter(user_id=user_id)
        
        if activity_type:
            activities_query = activities_query.filter(activity_type=activity_type)
        
        activities = activities_query.order_by('-timestamp')[:limit]
        
        activities_data = []
        for activity in activities:
            activities_data.append({
                'id': activity.id,
                'user': {
                    'id': activity.user.id,
                    'username': activity.user.username,
                    'uid': activity.user.uid
                },
                'activity_type': activity.activity_type,
                'description': activity.description,
                'ip_address': activity.ip_address,
                'user_agent': activity.user_agent,
                'timestamp': activity.timestamp.isoformat(),
                'metadata': activity.metadata
            })
        
        return JsonResponse({
            'success': True,
            'activities': activities_data,
            'total': len(activities_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["GET"])
def api_active_sessions(request):
    """API endpoint to get active user sessions"""
    try:
        sessions = UserSession.objects.filter(is_active=True).select_related('user').order_by('-last_activity')
        
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                'id': session.id,
                'user': {
                    'id': session.user.id,
                    'username': session.user.username,
                    'uid': session.user.uid
                },
                'session_id': session.session_id,
                'ip_address': session.ip_address,
                'user_agent': session.user_agent,
                'login_time': session.login_time.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'is_active': session.is_active
            })
        
        return JsonResponse({
            'success': True,
            'sessions': sessions_data,
            'total': len(sessions_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["GET"])
def api_system_info(request):
    """API endpoint to get system information"""
    try:
        system_info = SystemInfo.objects.first()
        
        if not system_info:
            system_info = SystemInfo.update_system_info()
        
        if system_info:
            info_data = {
                'hostname': system_info.hostname,
                'os_name': system_info.os_name,
                'os_version': system_info.os_version,
                'kernel_version': system_info.kernel_version,
                'architecture': system_info.architecture,
                'total_users': system_info.total_users,
                'active_users': system_info.active_users,
                'last_updated': system_info.last_updated.isoformat()
            }
            
            return JsonResponse({
                'success': True,
                'system_info': info_data
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'System information not available'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_user_action(request, user_id, action):
    """API endpoint to perform actions on users"""
    try:
        user = get_object_or_404(SystemUser, id=user_id)
        
        if action == 'get_info':
            # Get detailed system information for the user
            try:
                user_info = pwd.getpwnam(user.username)
                group_info = grp.getgrgid(user.gid)
                
                return JsonResponse({
                    'success': True,
                    'user_info': {
                        'username': user_info.pw_name,
                        'uid': user_info.pw_uid,
                        'gid': user_info.pw_gid,
                        'home_directory': user_info.pw_dir,
                        'shell': user_info.pw_shell,
                        'gecos': user_info.pw_gecos,
                        'group_name': group_info.gr_name,
                        'group_members': group_info.gr_mem
                    }
                })
            except KeyError:
                return JsonResponse({
                    'success': False,
                    'error': 'User not found in system'
                })
        
        else:
            return JsonResponse({
                'success': False,
                'error': f'Unknown action: {action}'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["GET"])
def api_user_stats(request):
    """API endpoint to get user statistics"""
    try:
        total_users = SystemUser.objects.count()
        active_users = SystemUser.objects.filter(is_active=True).count()
        system_users = SystemUser.objects.filter(is_system_user=True).count()
        real_users = SystemUser.objects.filter(is_system_user=False).count()
        
        # Get recent activities count
        recent_activities = UserActivity.objects.filter(
            timestamp__gte=datetime.now() - timedelta(hours=24)
        ).count()
        
        # Get active sessions count
        active_sessions = UserSession.objects.filter(is_active=True).count()
        
        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'system_users': system_users,
            'real_users': real_users,
            'recent_activities': recent_activities,
            'active_sessions': active_sessions
        }
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_create_user(request):
    """API endpoint to create a new system user"""
    try:
        data = json.loads(request.body)
        
        # Extract parameters
        username = data.get('username', '').strip()
        password = data.get('password', '')
        home_dir = data.get('home_dir', '').strip()
        shell = data.get('shell', '').strip()
        full_name = data.get('full_name', '').strip()
        create_home = data.get('create_home', True)
        system_user = data.get('system_user', False)
        
        # Validate required fields
        if not username:
            return JsonResponse({
                'success': False,
                'error': 'Username is required'
            })
        
        # Validate username format
        if not username.replace('_', '').replace('-', '').isalnum():
            return JsonResponse({
                'success': False,
                'error': 'Username can only contain letters, numbers, underscores, and hyphens'
            })
        
        # Create user using model method
        result = SystemUser.create_user(
            username=username,
            password=password if password else None,
            home_dir=home_dir if home_dir else None,
            shell=shell if shell else None,
            full_name=full_name if full_name else None,
            create_home=create_home,
            system_user=system_user
        )
        
        if result['success']:
            # Log the activity
            UserActivity.objects.create(
                user=None,  # Will be set after user creation
                activity_type='user_created',
                description=f'User {username} created via web interface',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                metadata={
                    'created_by': request.user.username if request.user.is_authenticated else 'anonymous',
                    'home_directory': result.get('home_directory', ''),
                    'uid': result.get('uid', ''),
                    'system_user': system_user
                }
            )
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_delete_user(request, username):
    """API endpoint to delete a system user"""
    try:
        data = json.loads(request.body)
        
        # Extract parameters
        remove_home = data.get('remove_home', False)
        remove_files = data.get('remove_files', False)
        
        # Validate username
        if not username:
            return JsonResponse({
                'success': False,
                'error': 'Username is required'
            })
        
        # Delete user using model method
        result = SystemUser.delete_user(
            username=username,
            remove_home=remove_home,
            remove_files=remove_files
        )
        
        if result['success']:
            # Log the activity
            UserActivity.objects.create(
                user=None,
                activity_type='user_deleted',
                description=f'User {username} deleted via web interface',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                metadata={
                    'deleted_by': request.user.username if request.user.is_authenticated else 'anonymous',
                    'removed_home': remove_home,
                    'removed_files': remove_files
                }
            )
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_modify_user(request, username):
    """API endpoint to modify an existing user"""
    try:
        data = json.loads(request.body)
        
        # Extract parameters
        home_dir = data.get('home_dir', '').strip()
        shell = data.get('shell', '').strip()
        full_name = data.get('full_name', '').strip()
        lock = data.get('lock', None)
        
        # Prepare modification parameters
        modify_params = {}
        
        if home_dir:
            modify_params['home_dir'] = home_dir
        if shell:
            modify_params['shell'] = shell
        if full_name:
            modify_params['full_name'] = full_name
        if lock is not None:
            modify_params['lock'] = lock
        
        # Validate username
        if not username:
            return JsonResponse({
                'success': False,
                'error': 'Username is required'
            })
        
        # Modify user using model method
        result = SystemUser.modify_user(username, **modify_params)
        
        if result['success']:
            # Log the activity
            UserActivity.objects.create(
                user=None,  # Will be set after user lookup
                activity_type='user_modified',
                description=f'User {username} modified via web interface',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                metadata={
                    'modified_by': request.user.username if request.user.is_authenticated else 'anonymous',
                    'modifications': modify_params
                }
            )
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required


@csrf_exempt
def api_create_user(request):
    """API endpoint to create a new system user"""
    try:
        data = json.loads(request.body)
        
        # Extract parameters
        username = data.get('username', '').strip() if data.get('username') else ''
        password = data.get('password', '') if data.get('password') else ''
        home_directory = data.get('home_directory', '').strip() if data.get('home_directory') else ''
        root_dir = data.get('root_dir', '').strip() if data.get('root_dir') else ''
        grant_sudo = data.get('grant_sudo', False)
        
        # Validate required fields
        if not username:
            return JsonResponse({
                'success': False,
                'error': 'Username is required'
            })
        
        if not password:
            return JsonResponse({
                'success': False,
                'error': 'Password is required'
            })
        
        # Validate username format
        if not username.replace('_', '').replace('-', '').isalnum():
            return JsonResponse({
                'success': False,
                'error': 'Username can only contain letters, numbers, underscores, and hyphens'
            })
        
        # Check if user already exists
        try:
            pwd.getpwnam(username)
            return JsonResponse({
                'success': False,
                'error': f'User {username} already exists'
            })
        except KeyError:
            pass  # User doesn't exist, which is good
        
        # Build useradd command
        command = ['useradd', '-m']
        
        if home_directory:
            command.extend(['-d', home_directory])
        if root_dir:
            command.extend(['-R', root_dir])
        
        command.append(username)
        
        # Execute useradd command
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to create user: {e}'
            })

        # Set password using chpasswd
        try:
            subprocess.run(['chpasswd'], input=f"{username}:{password}".encode(), check=True)
        except subprocess.CalledProcessError as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to set password: {e}'
            })

        # Grant sudo privileges if requested
        if grant_sudo:
            try:
                # Add user to sudo group
                subprocess.run(['usermod', '-aG', 'sudo', username], check=True)
            except subprocess.CalledProcessError as e:
                # If sudo group doesn't exist, try wheel group (some systems use wheel)
                try:
                    subprocess.run(['usermod', '-aG', 'wheel', username], check=True)
                except subprocess.CalledProcessError as e2:
                    return JsonResponse({
                        'success': False,
                        'error': f'Failed to grant sudo privileges: {e2}'
                    })

        # Sync users to update database
        SystemUser.sync_system_users()
        
        # Prepare success message
        message = f'User {username} created successfully'
        if grant_sudo:
            message += ' with sudo privileges'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'username': username
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        })


@csrf_exempt
def api_delete_user(request, username):
    """API endpoint to delete a system user"""
    try:
        # Validate username
        if not username or not username.strip():
            return JsonResponse({
                'success': False,
                'error': 'Username is required'
            })
        
        username = username.strip()
        
        # Check if user exists in system
        try:
            pwd.getpwnam(username)
        except KeyError:
            return JsonResponse({
                'success': False,
                'error': f'User {username} does not exist'
            })
        
        # Prevent deletion of root user
        if username == 'root':
            return JsonResponse({
                'success': False,
                'error': 'Cannot delete root user'
            })
        
        # Delete user from system using userdel
        try:
            # Use -r flag to remove home directory as well
            subprocess.run(['userdel', '-r', username], check=True)
        except subprocess.CalledProcessError as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to delete user: {e}'
            })
        
        # Remove user from database
        try:
            SystemUser.objects.filter(username=username).delete()
        except Exception as e:
            # Log the error but don't fail the operation
            print(f"Warning: Could not remove user {username} from database: {e}")
        
        return JsonResponse({
            'success': True,
            'message': f'User {username} deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        })

@login_required
@require_http_methods(["GET"])
def api_user_permissions(request, user_id):
    """API endpoint to get detailed user permissions"""
    try:
        user = get_object_or_404(SystemUser, id=user_id)
        
        # Get comprehensive user permissions
        permissions = user.get_user_permissions()
        
        return JsonResponse({
            'success': True,
            'permissions': permissions
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })