from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from common.timezone.utils import get_user_timezone, set_user_timezone, format_dt
import json
import sys
import os
import re
import logging

logger = logging.getLogger(__name__)

# Error log modülünü import et
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from common.error_log.error_log import log_login_attempt, log_security_event
# Rate limiter removed per request; no IP-based checks

def validate_password_strength(password):
    """Strong password policy validation"""
    errors = []
    
    # Minimum length
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    
    # Uppercase check
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least 1 uppercase letter')
    
    # Lowercase check
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least 1 lowercase letter')
    
    # Digit check
    if not re.search(r'[0-9]', password):
        errors.append('Password must contain at least 1 digit')
    
    # Special character check
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        errors.append('Password must contain at least 1 special character (!@#$%^&* etc.)')
    
    # Common passwords check
    common_passwords = [
        'password', '123456', '123456789', 'qwerty', 'abc123', 
        'password123', 'admin', 'letmein', 'welcome', 'monkey',
        '1234567890', 'password1', 'qwerty123', 'dragon', 'master'
    ]
    if password.lower() in common_passwords:
        errors.append('Commonly used passwords are not secure')
    
    # Repeating characters check
    if re.search(r'(.)\1{2,}', password):
        errors.append('Password should not contain repeated characters (aaa, 111, etc.)')
    
    # Keyboard sequence check
    keyboard_sequences = [
        'qwerty', 'asdfgh', 'zxcvbn', '123456', 'abcdef',
        'qwertyuiop', 'asdfghjkl', 'zxcvbnm'
    ]
    password_lower = password.lower()
    for sequence in keyboard_sequences:
        if sequence in password_lower or sequence[::-1] in password_lower:
            errors.append('Keyboard sequence passwords are not secure')
    
    return errors

def login_view(request):
    """Login page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # 2FA check
                from common.security.models import TwoFactorAuth
                try:
                    two_factor = TwoFactorAuth.objects.get(user=user)
                    if two_factor.is_enabled:
                        # 2FA enabled: store user in session but do not log in
                        request.session['pending_2fa_user'] = user.id
                        request.session['pending_2fa_username'] = username
                        log_login_attempt(request, username, success=True, failure_reason='2FA pending')
                        
                        return JsonResponse({
                            'success': True,
                            'message': '2FA verification required',
                            'requires_2fa': True,
                            'redirect': '/login/2fa/'
                        })
                except TwoFactorAuth.DoesNotExist:
                    pass
                
                # No 2FA or disabled: normal login
                log_login_attempt(request, username, success=True)
                login(request, user)
                
                # Session tracking - session key is created after login
                try:
                    from common.security.models import UserSession
                    # Save session to obtain session key
                    request.session.save()
                    UserSession.create_session(user, request.session.session_key, request)
                except Exception as e:
                    pass  # Continue even if session tracking fails
                
                # Log activity
                from common.security.models import UserActivity
                UserActivity.log_activity(
                    user=user,
                    activity_type='login',
                    title='Login Successful',
                    description='Successfully signed in to the account',
                    status='success',
                    request=request
                )
                
                return JsonResponse({'success': True, 'redirect': '/dashboard/'})
            else:
                # Failed login - log and increase attempt count
                log_login_attempt(request, username, success=False, failure_reason='Invalid credentials')
                
                # Log failed login activity
                try:
                    from common.security.models import UserActivity
                    UserActivity.log_activity(
                        user=None,  # User not found
                        activity_type='failed_login',
                        title='Failed Login Attempt',
                        description=f'Login attempt with incorrect password: {username}',
                        status='failed',
                        request=request
                    )
                except:
                    pass  # Continue even if activity logging fails
                
                # Check remaining attempts
                remaining_attempts = MAX_ATTEMPTS if 'MAX_ATTEMPTS' in globals() else 5
                
                if remaining_attempts <= 0:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Too many failed attempts. Please try again in 5 minutes.',
                        'rate_limited': True
                    })
                else:
                    return JsonResponse({
                        'success': False, 
                        'error': f'Invalid username or password. Remaining attempts: {remaining_attempts}',
                        'remaining_attempts': remaining_attempts
                    })
        else:
            # Missing credentials - log and increase attempt count
            attempted_username = username or 'Empty'
            log_login_attempt(request, attempted_username, success=False, failure_reason='Missing credentials')
            
            # Check remaining attempts
            remaining_attempts = MAX_ATTEMPTS if 'MAX_ATTEMPTS' in globals() else 5
            
            if remaining_attempts <= 0:
                return JsonResponse({
                    'success': False, 
                    'error': 'Too many failed attempts. Please try again in 5 minutes.',
                    'rate_limited': True
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': f'Please fill in all fields. Remaining attempts: {remaining_attempts}',
                    'remaining_attempts': remaining_attempts
                })
    
    return render(request, 'pages/login.html')

@login_required
def dashboard_view(request):
    """Dashboard page - only authenticated users can access"""
    # Check if user profile is complete
    from common.profile.models import UserProfile
    
    # Get or create profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Check if profile is complete
    if not profile.is_profile_complete:
        # Check if required fields are filled
        if not profile.full_name or not profile.email or not profile.timezone:
            return redirect('profile_setup')
        else:
            # Mark as complete if all fields are filled
            profile.is_profile_complete = True
            profile.save()
    
    return render(request, 'pages/dashboard.html')

def logout_view(request):
    """Logout process"""
    # End session
    if request.user.is_authenticated:
        try:
            from common.security.models import UserSession
            UserSession.end_session(request.session.session_key)
        except:
            pass  # Continue even if session end fails
        
        # Log logout activity
        try:
            from common.security.models import UserActivity
            UserActivity.log_activity(
                user=request.user,
                activity_type='logout',
                title='Logged Out',
                description='Signed out of the account',
                status='success',
                request=request
            )
        except:
            pass  # Continue even if activity logging fails
    
    logout(request)
    return redirect('login')

def settings_view(request):
    """Settings page"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Ensure user has a profile
    from common.profile.models import UserProfile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    try:
        from django.contrib.auth.models import Permission
        # Direct user permissions
        user_perms = Permission.objects.filter(user=request.user)
        # Permissions via groups
        group_perms = Permission.objects.filter(group__user=request.user)
        permission_names = list((user_perms | group_perms).distinct().values_list('name', flat=True))
    except Exception:
        permission_names = []
    
    return render(request, 'pages/settings/settings.html', {
        'permission_names': permission_names,
        'user_profile': profile,  # Add profile to context
    })

def activity_history_view(request):
    """Account activity history page"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    return render(request, 'pages/security/activity-history.html')

def alert_management_view(request):
    """Alert management page"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    return render(request, 'pages/security/alert-management.html')

# Removed active_sessions_view per request (IP/session UI removed)

def profile_upload_view(request):
    """Profile image upload API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'errors': ['Authentication required']})
    
    if request.method == 'POST':
        try:
            from common.profile.models import UserProfile
            
            if 'profile_image' not in request.FILES:
                return JsonResponse({'success': False, 'errors': ['Resim dosyası bulunamadı']})
            
            file = request.FILES['profile_image']
            
            # File validation
            max_size = 5 * 1024 * 1024  # 5MB
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            
            if file.size > max_size:
                return JsonResponse({'success': False, 'errors': ['File size cannot exceed 5MB']})
            
            if file.content_type not in allowed_types:
                return JsonResponse({'success': False, 'errors': ['Unsupported file format']})
            
            # Profil oluştur veya güncelle
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.profile_image = file
            profile.save()
            
            # Log profile image upload activity
            try:
                from common.security.models import UserActivity
                UserActivity.log_activity(
                    user=request.user,
                    activity_type='profile_image_upload',
                    title='Profile Image Uploaded',
                    description='New profile image uploaded',
                    status='success',
                    request=request
                )
            except:
                pass  # Aktivite loglama başarısız olsa bile devam et
            
            return JsonResponse({
                'success': True,
                'message': 'Profile image updated successfully',
                'url': profile.profile_image_url
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'errors': [f'Unexpected error: {str(e)}']})
    
    return JsonResponse({'success': False, 'errors': ['Invalid request']})

def profile_remove_view(request):
    """Profile image removal API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'errors': ['Authentication required']})
    
    if request.method == 'POST':
        try:
            from common.profile.models import UserProfile
            
            try:
                profile = UserProfile.objects.get(user=request.user)
                profile.delete_profile_image()
                
                # Log profile image removal activity
                try:
                    from common.security.models import UserActivity
                    UserActivity.log_activity(
                        user=request.user,
                        activity_type='profile_image_remove',
                        title='Profile Image Removed',
                        description='Profile image removed',
                        status='success',
                        request=request
                    )
                except:
                    pass  # Aktivite loglama başarısız olsa bile devam et
                
                return JsonResponse({'success': True, 'message': 'Profile image removed'})
            except UserProfile.DoesNotExist:
                return JsonResponse({'success': True, 'message': 'No profile image exists'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'errors': [f'Unexpected error: {str(e)}']})
    
    return JsonResponse({'success': False, 'errors': ['Invalid request']})

def profile_check_view(request, username):
    """Profile image check API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'errors': ['Authentication required']})
    
    try:
        from common.profile.models import UserProfile
        
        try:
            profile = UserProfile.objects.get(user__username=username)
            return JsonResponse({
                'success': True,
                'has_profile': profile.has_profile_image,
                'url': profile.profile_image_url
            })
        except UserProfile.DoesNotExist:
            return JsonResponse({
                'success': True,
                'has_profile': False,
                'url': '/static/images/demo-avatar.svg'
            })
        
    except Exception as e:
        return JsonResponse({'success': False, 'errors': [f'Unexpected error: {str(e)}']})

def password_change_view(request):
    """Password change API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'errors': ['Authentication required']})
    
    if request.method == 'POST':
        try:
            from django.contrib.auth import authenticate
            import json
            
            data = json.loads(request.body)
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')
            
            # Validation
            if not current_password or not new_password or not confirm_password:
                return JsonResponse({'success': False, 'errors': ['Please fill in all fields']})
            
            if new_password != confirm_password:
                return JsonResponse({'success': False, 'errors': ['New passwords do not match']})
            
            # Strong password policy check
            password_errors = validate_password_strength(new_password)
            if password_errors:
                return JsonResponse({'success': False, 'errors': password_errors})
            
            # Check current password
            user = authenticate(username=request.user.username, password=current_password)
            if not user:
                return JsonResponse({'success': False, 'errors': ['Current password is incorrect']})
            
            # Change password
            request.user.set_password(new_password)
            request.user.save()
            
            # Log password change activity
            try:
                from common.security.models import UserActivity
                UserActivity.log_activity(
                    user=request.user,
                    activity_type='password_change',
                    title='Password Changed',
                    description='Account password updated successfully',
                    status='success',
                    request=request
                )
            except:
                pass  # Aktivite loglama başarısız olsa bile devam et
            
            # Logout user for security
            from django.contrib.auth import logout
            logout(request)
            
            return JsonResponse({
                'success': True,
                'message': 'Password changed successfully. For security, you need to sign in again.'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': ['Invalid data format']})
        except Exception as e:
            return JsonResponse({'success': False, 'errors': [f'Unexpected error: {str(e)}']})
    
    return JsonResponse({'success': False, 'errors': ['Invalid request']})

def two_factor_setup_view(request):
    """2FA setup API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'errors': ['Authentication required']})
    
    if request.method == 'POST':
        try:
            from common.security.models import TwoFactorAuth
            
            two_factor, created = TwoFactorAuth.objects.get_or_create(user=request.user)
            
            # QR kod oluştur
            qr_code_base64, provisioning_uri = two_factor.generate_qr_code()
            
            return JsonResponse({
                'success': True,
                'qr_code': qr_code_base64,
                'secret_key': two_factor.secret_key,
                'provisioning_uri': provisioning_uri
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'errors': [f'Unexpected error: {str(e)}']})
    
    return JsonResponse({'success': False, 'errors': ['Invalid request']})

def two_factor_verify_view(request):
    """2FA verification API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'errors': ['Authentication required']})
    
    if request.method == 'POST':
        try:
            from common.security.models import TwoFactorAuth
            import json
            
            data = json.loads(request.body)
            token = data.get('token')
            
            if not token:
                return JsonResponse({'success': False, 'errors': ['Token is required']})
            
            two_factor = TwoFactorAuth.objects.get(user=request.user)
            
            if two_factor.verify_token(token):
                two_factor.is_enabled = True
                two_factor.save()
                
                # Log 2FA enable activity
                try:
                    from common.security.models import UserActivity
                    UserActivity.log_activity(
                        user=request.user,
                        activity_type='2fa_enable',
                        title='2FA Enabled',
                        description='Two-factor authentication has been enabled',
                        status='warning',
                        request=request
                    )
                except:
                    pass  # Aktivite loglama başarısız olsa bile devam et
                
                # Yedek kodlar oluştur
                backup_codes = two_factor.generate_backup_codes()
                
                return JsonResponse({
                    'success': True,
                    'message': '2FA enabled successfully',
                    'backup_codes': backup_codes
                })
            else:
                return JsonResponse({'success': False, 'errors': ['Invalid token']})
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': ['Invalid data format']})
        except Exception as e:
            return JsonResponse({'success': False, 'errors': [f'Unexpected error: {str(e)}']})
    
    return JsonResponse({'success': False, 'errors': ['Invalid request']})

def two_factor_disable_view(request):
    """2FA disable API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'errors': ['Authentication required']})
    
    if request.method == 'POST':
        try:
            from common.security.models import TwoFactorAuth
            from django.contrib.auth import authenticate
            import json
            
            data = json.loads(request.body)
            password = data.get('password')
            token = data.get('token')
            
            # Password validation
            if not password:
                return JsonResponse({'success': False, 'errors': ['Password is required']})
            
            user = authenticate(username=request.user.username, password=password)
            if not user:
                return JsonResponse({'success': False, 'errors': ['Incorrect password']})
            
            # 2FA validation
            two_factor = TwoFactorAuth.objects.get(user=request.user)
            if not two_factor.is_enabled:
                return JsonResponse({'success': False, 'errors': ['2FA is already disabled']})
            
            # 2FA token validation
            if not token:
                return JsonResponse({'success': False, 'errors': ['2FA code is required']})
            
            # Validate TOTP token or backup code
            if not two_factor.verify_token(token) and not two_factor.verify_backup_code(token):
                return JsonResponse({'success': False, 'errors': ['Invalid 2FA code']})
            
            # Disable 2FA
            two_factor.is_enabled = False
            two_factor.secret_key = None
            two_factor.backup_codes = []
            two_factor.save()
            
            # Log 2FA disable activity
            try:
                from common.security.models import UserActivity
                UserActivity.log_activity(
                    user=request.user,
                    activity_type='2fa_disable',
                    title='2FA Disabled',
                    description='Two-factor authentication has been disabled',
                    status='warning',
                    request=request
                )
            except:
                pass  # Aktivite loglama başarısız olsa bile devam et
            
            return JsonResponse({
                'success': True,
                'message': '2FA disabled successfully'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': ['Invalid data format']})
        except Exception as e:
            return JsonResponse({'success': False, 'errors': [f'Unexpected error: {str(e)}']})
    
    return JsonResponse({'success': False, 'errors': ['Invalid request']})

def two_factor_status_view(request):
    """2FA status API - for 2FA login process"""
    # Session check - for pending 2FA user
    if not request.session.get('pending_2fa_user'):
        return JsonResponse({'success': False, 'errors': ['2FA session not found']})
    
    try:
        from common.security.models import TwoFactorAuth
        from django.contrib.auth import get_user_model
        
        # Get user info from session
        user_id = request.session.get('pending_2fa_user')
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'errors': ['User not found']})
        
        two_factor = TwoFactorAuth.objects.get(user=user)
        
        return JsonResponse({
            'success': True,
            'is_enabled': two_factor.is_enabled,
            'has_backup_codes': len(two_factor.backup_codes) > 0
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'errors': [f'Unexpected error: {str(e)}']})

def two_factor_settings_status_view(request):
    """2FA status API - for Settings page"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'errors': ['Authentication required']})
    
    try:
        from common.security.models import TwoFactorAuth
        
        try:
            two_factor = TwoFactorAuth.objects.get(user=request.user)
            return JsonResponse({
                'success': True,
                'is_enabled': two_factor.is_enabled,
                'has_backup_codes': len(two_factor.backup_codes) > 0
            })
        except TwoFactorAuth.DoesNotExist:
            # No 2FA record, not enabled
            return JsonResponse({
                'success': True,
                'is_enabled': False,
                'has_backup_codes': False
            })
        
    except Exception as e:
        return JsonResponse({'success': False, 'errors': [f'Beklenmeyen hata: {str(e)}']})

def two_factor_verify_login_view(request):
    """2FA login verification API"""
    if request.method == 'POST':
        try:
            from common.security.models import TwoFactorAuth
            from django.contrib.auth import get_user_model
            import json
            
            data = json.loads(request.body)
            token = data.get('token')
            is_backup_code = data.get('is_backup_code', False)
            
            if not token:
                return JsonResponse({'success': False, 'error': 'Token is required'})
            
            # Get user info from session
            user_id = request.session.get('pending_2fa_user')
            username = request.session.get('pending_2fa_username')
            
            if not user_id or not username:
                return JsonResponse({'success': False, 'error': '2FA session not found'})
            
            # Get user
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'User not found'})
            
            # 2FA verification
            try:
                two_factor = TwoFactorAuth.objects.get(user=user)
            except TwoFactorAuth.DoesNotExist:
                return JsonResponse({'success': False, 'error': '2FA kaydı bulunamadı'})
            
            # Verification process
            verification_success = False
            try:
                if is_backup_code:
                    # Backup code verification
                    verification_success = two_factor.verify_backup_code(token)
                else:
                    # TOTP token verification
                    verification_success = two_factor.verify_token(token)
            except Exception as e:
                print(f"2FA Verification Error: {str(e)}")
                return JsonResponse({'success': False, 'error': 'An error occurred during 2FA verification'})
            
            if not verification_success:
                error_msg = 'Invalid backup code' if is_backup_code else 'Invalid 2FA code'
                return JsonResponse({'success': False, 'error': error_msg})
            
            # Successful verification - log user in
            login(request, user)
            
            # Session tracking - session key is created after login
            try:
                from common.security.models import UserSession
                # Save session to obtain session key
                request.session.save()
                UserSession.create_session(user, request.session.session_key, request)
            except Exception as e:
                pass  # Continue even if session tracking fails
            
            # Log 2FA verification activity
            try:
                from common.security.models import UserActivity
                UserActivity.log_activity(
                    user=user,
                    activity_type='2fa_verify',
                    title='2FA Verified',
                    description='Two-factor authentication was completed successfully',
                    status='success',
                    request=request
                )
            except:
                pass  # Continue even if activity logging fails
            
            # Clear session
            if 'pending_2fa_user' in request.session:
                del request.session['pending_2fa_user']
            if 'pending_2fa_username' in request.session:
                del request.session['pending_2fa_username']
            
            # Log
            log_login_attempt(request, username, True, '2FA verified')
            
            return JsonResponse({
                'success': True,
                'message': '2FA verification successful',
                'redirect': '/dashboard/'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid data format'})
        except Exception as e:
            # Debug için detaylı hata logu
            import traceback
            print(f"2FA Verification Error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def login_2fa_view(request):
    """2FA doğrulama sayfası"""
    # Session kontrolü
    if not request.session.get('pending_2fa_user'):
        return redirect('login')
    
    return render(request, 'pages/login-2fa.html')

def activity_list_view(request):
    """Activity list API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    try:
        from common.security.models import UserActivity
        from django.core.paginator import Paginator
        from django.utils import timezone
        from datetime import timedelta
        import json
        
        # Filtering parameters
        activity_type = request.GET.get('type', '')
        status_filter = request.GET.get('status', '')
        date_range = int(request.GET.get('date_range', 30))
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        # Debug logging
        print(f"Activity API Debug - Type: {activity_type}, Status: {status_filter}, Date Range: {date_range}")
        
        # Date filter
        end_date = timezone.now()
        start_date = end_date - timedelta(days=date_range)
        
        # Build query
        activities = UserActivity.objects.filter(
            user=request.user,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Additional filters
        if activity_type:
            activities = activities.filter(activity_type=activity_type)
            print(f"Filtered by activity_type: {activity_type}")
        
        if status_filter:
            activities = activities.filter(status=status_filter)
            print(f"Filtered by status: {status_filter}")
        
        print(f"Total activities found: {activities.count()}")
        
        # Pagination
        paginator = Paginator(activities, per_page)
        page_obj = paginator.get_page(page)
        
        # Prepare data
        user_tz = get_user_timezone(request)
        activities_data = []
        for activity in page_obj:
            # Apply timezone to created_at for display fields
            created_dt = activity.created_at
            activities_data.append({
                'id': activity.id,
                'activity_type': activity.activity_type,
                'title': activity.title,
                'description': activity.description,
                'status': activity.status,
                'created_at': format_dt(created_dt, user_tz, '%Y-%m-%d %H:%M:%S'),
                'created_at_display': format_dt(created_dt, user_tz, '%Y-%m-%d %H:%M'),
                'icon_class': activity.get_icon_class(),
                'status_class': activity.get_status_class(),
                'metadata': activity.metadata
            })
        
        return JsonResponse({
            'success': True,
            'activities': activities_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })
        
    except Exception as e:
        print(f"Activity API Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})

def alert_list_view(request):
    """Alert list API for management page"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    try:
        from common.dashboard.models import SystemAlert
        from django.core.paginator import Paginator
        from django.utils import timezone
        from datetime import timedelta
        import json
        
        # Filtering parameters
        alert_type = request.GET.get('type', '')
        status_filter = request.GET.get('status', '')
        date_range = int(request.GET.get('date_range', 30))
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        # Date filter
        end_date = timezone.now()
        start_date = end_date - timedelta(days=date_range)
        
        # Build query
        alerts = SystemAlert.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Additional filters
        if alert_type:
            alerts = alerts.filter(alert_type=alert_type)
        
        if status_filter == 'resolved':
            alerts = alerts.filter(is_resolved=True)
        elif status_filter == 'unresolved':
            alerts = alerts.filter(is_resolved=False)
        
        # Order by created_at desc
        alerts = alerts.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(alerts, per_page)
        page_obj = paginator.get_page(page)
        
        # Prepare data
        alerts_data = []
        for alert in page_obj:
            alerts_data.append({
                'id': alert.id,
                'type': alert.alert_type,
                'title': alert.title,
                'message': alert.message,
                'service': alert.service.display_name if alert.service else None,
                'service_category': alert.service.category if alert.service else None,
                'is_resolved': alert.is_resolved,
                'created_at': alert.created_at.isoformat(),
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                'notes': alert.notes or '',
                'icon': alert.get_alert_icon(),
                'metadata': alert.metadata
            })
        
        return JsonResponse({
            'success': True,
            'alerts': alerts_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def alert_export_view(request):
    """Alert export API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    try:
        from common.dashboard.models import SystemAlert
        from django.utils import timezone
        from datetime import timedelta
        import csv
        from django.http import HttpResponse
        
        # Filtering parameters
        alert_type = request.GET.get('type', '')
        status_filter = request.GET.get('status', '')
        date_range = int(request.GET.get('date_range', 30))
        export_format = request.GET.get('export', 'csv')
        
        # Date filter
        end_date = timezone.now()
        start_date = end_date - timedelta(days=date_range)
        
        # Build query
        alerts = SystemAlert.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Additional filters
        if alert_type:
            alerts = alerts.filter(alert_type=alert_type)
        
        if status_filter == 'resolved':
            alerts = alerts.filter(is_resolved=True)
        elif status_filter == 'unresolved':
            alerts = alerts.filter(is_resolved=False)
        
        # Order by created_at desc
        alerts = alerts.order_by('-created_at')
        
        if export_format.lower() == 'csv':
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="alerts_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'ID', 'Type', 'Title', 'Message', 'Service', 'Service Category',
                'Is Resolved', 'Created At', 'Resolved At', 'Metadata'
            ])
            
            for alert in alerts:
                writer.writerow([
                    alert.id,
                    alert.alert_type,
                    alert.title,
                    alert.message,
                    alert.service.display_name if alert.service else '',
                    alert.service.category if alert.service else '',
                    alert.is_resolved,
                    alert.created_at.isoformat(),
                    alert.resolved_at.isoformat() if alert.resolved_at else '',
                    str(alert.metadata) if alert.metadata else ''
                ])
            
            return response
        
        else:
            return JsonResponse({
                'success': False,
                'error': 'Unsupported export format'
            }, status=400)
        
    except Exception as e:
        logger.error(f"Error exporting alerts: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def alert_add_note_view(request, alert_id):
    """Add note to alert"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    try:
        from common.dashboard.models import SystemAlert
        import json
        
        data = json.loads(request.body)
        note = data.get('note', '').strip()
        
        if not note:
            return JsonResponse({
                'success': False,
                'error': 'Note cannot be empty'
            }, status=400)
        
        alert = SystemAlert.objects.get(id=alert_id)
        alert.notes = note
        alert.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Note added successfully'
        })
        
    except SystemAlert.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Alert not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error adding note to alert {alert_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def activity_export_view(request):
    """Activity export API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    try:
        from common.security.models import UserActivity
        from django.utils import timezone
        from datetime import timedelta
        import csv
        from django.http import HttpResponse
        
        # Filtering parameters
        activity_type = request.GET.get('type', '')
        status_filter = request.GET.get('status', '')
        date_range = int(request.GET.get('date_range', 30))
        
        # Date filter
        end_date = timezone.now()
        start_date = end_date - timedelta(days=date_range)
        
        # Build query
        activities = UserActivity.objects.filter(
            user=request.user,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Additional filters
        if activity_type:
            activities = activities.filter(activity_type=activity_type)
        
        if status_filter:
            activities = activities.filter(status=status_filter)
        
        # Build CSV response
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="activity_history_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Add BOM (for Excel compatibility)
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow([
            'Date', 'Activity Type', 'Title', 'Description', 'Status'
        ])
        
        user_tz = get_user_timezone(request)

        for activity in activities:
            export_dt = activity.created_at
            writer.writerow([
                format_dt(export_dt, user_tz, '%Y-%m-%d %H:%M:%S'),
                activity.get_activity_type_display(),
                activity.title,
                activity.description,
                activity.get_status_display()
            ])
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})

def profile_update_view(request):
    """Profile update API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    if request.method == 'POST':
        try:
            import json
            from common.profile.models import UserProfile
            
            data = json.loads(request.body)
            
            # Get or create user profile
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            
            # Update profile fields
            if 'full_name' in data:
                profile.full_name = data['full_name']
            if 'email' in data:
                profile.email = data['email']
            if 'timezone' in data:
                profile.timezone = data['timezone']
            if 'language' in data:
                profile.language = data['language']
            
            profile.save()
            
            # Log profile update activity
            try:
                from common.security.models import UserActivity
                UserActivity.log_activity(
                    user=request.user,
                    activity_type='profile_update',
                    title='Profile Updated',
                    description='Profile information updated',
                    status='success',
                    request=request
                )
            except:
                pass
            
            return JsonResponse({'success': True, 'message': 'Profile updated successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def email_change_view(request):
    """Email change API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            new_email = data.get('email')
            
            if not new_email:
                return JsonResponse({'success': False, 'error': 'Email address is required'})
            
            # Log email change activity
            try:
                from common.security.models import UserActivity
                UserActivity.log_activity(
                    user=request.user,
                    activity_type='email_change',
                    title='Email Changed',
                    description=f'Email address updated to {new_email}',
                    status='success',
                    request=request
                )
            except:
                pass
            
            return JsonResponse({'success': True, 'message': 'Email address updated successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def name_change_view(request):
    """Name change API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            new_name = data.get('name')
            
            if not new_name:
                return JsonResponse({'success': False, 'error': 'Full name is required'})
            
            # Log name change activity
            try:
                from common.security.models import UserActivity
                UserActivity.log_activity(
                    user=request.user,
                    activity_type='name_change',
                    title='Name Changed',
                    description=f'Full name updated to {new_name}',
                    status='success',
                    request=request
                )
            except:
                pass
            
            return JsonResponse({'success': True, 'message': 'Full name updated successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def language_change_view(request):
    """Language change API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    if request.method == 'POST':
        try:
            import json
            from common.profile.models import UserProfile
            from django.utils import translation
            from django.conf import settings
            
            data = json.loads(request.body)
            new_language = data.get('language')
            
            if not new_language:
                return JsonResponse({'success': False, 'error': 'Language selection is required'})
            
            # Validate language
            valid_languages = [lang[0] for lang in settings.LANGUAGES]
            if new_language not in valid_languages:
                return JsonResponse({'success': False, 'error': 'Invalid language selection'})
            
            # Update user profile
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.language = new_language
            profile.save()
            
            # Activate language for current session
            translation.activate(new_language)
            request.session[translation.LANGUAGE_SESSION_KEY] = new_language
            
            # Log language change activity
            try:
                from common.security.models import UserActivity
                UserActivity.log_activity(
                    user=request.user,
                    activity_type='language_change',
                    title='Language Changed',
                    description=f'Language preference updated to {new_language}',
                    status='success',
                    request=request
                )
            except:
                pass
            
            return JsonResponse({
                'success': True, 
                'message': 'Language preference updated successfully',
                'language': new_language
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def timezone_change_view(request):
    """Timezone change API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            new_timezone = data.get('timezone')
            
            if not new_timezone:
                return JsonResponse({'success': False, 'error': 'Timezone selection is required'})
            
            # Persist timezone in session via utils and log activity
            set_user_timezone(request, new_timezone)
            try:
                from common.security.models import UserActivity
                UserActivity.log_activity(
                    user=request.user,
                    activity_type='timezone_change',
                    title='Timezone Changed',
                    description=f'Timezone updated to {new_timezone}',
                    status='success',
                    request=request
                )
            except:
                pass
            
            return JsonResponse({'success': True, 'message': 'Timezone updated successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def timezone_list_view(request):
    """Public API: list all supported timezone names and current selection."""
    from common.timezone.utils import list_timezones
    try:
        tzs = list_timezones()
        # Get current timezone from user profile first, then session, then default
        current = 'UTC'
        if request.user.is_authenticated:
            try:
                from common.profile.models import UserProfile
                profile = UserProfile.objects.get(user=request.user)
                if profile.timezone:
                    current = profile.timezone
            except:
                pass
        
        # Fallback to session if no profile timezone
        if current == 'UTC':
            current = request.session.get('user_timezone') or 'UTC'
            
        return JsonResponse({'success': True, 'timezones': tzs, 'current': current})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



def profile_setup_view(request):
    """Profile setup page - first time users must complete their profile"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Check if profile is already complete
    from common.profile.models import UserProfile
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.is_profile_complete:
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        profile = UserProfile.objects.create(user=request.user)
    
    return render(request, 'pages/profile-setup.html')

def profile_setup_complete_view(request):
    """Complete profile setup API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    if request.method == 'POST':
        try:
            import json
            from common.profile.models import UserProfile
            
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['full_name', 'email', 'timezone']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({'success': False, 'error': f'{field.replace("_", " ").title()} is required'})
            
            # Get or create user profile
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            
            # Update profile fields
            profile.full_name = data['full_name']
            profile.email = data['email']
            profile.timezone = data['timezone']
            profile.language = data.get('language', 'en')
            
            # Handle profile image if provided
            if 'profile_image' in request.FILES:
                profile.profile_image = request.FILES['profile_image']
            
            # Mark profile as complete
            profile.is_profile_complete = True
            profile.save()
            
            # Log profile setup activity
            try:
                from common.security.models import UserActivity
                UserActivity.log_activity(
                    user=request.user,
                    activity_type='profile_setup',
                    title='Profile Setup Completed',
                    description='Initial profile setup completed',
                    status='success',
                    request=request
                )
            except:
                pass
            
            return JsonResponse({'success': True, 'message': 'Profile setup completed successfully', 'redirect': '/dashboard/'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def profile_complete_view(request):
    """Mark profile as complete API"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    if request.method == 'POST':
        try:
            from common.profile.models import UserProfile
            
            # Get or create user profile
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            
            # Mark profile as complete
            profile.is_profile_complete = True
            profile.save()
            
            return JsonResponse({'success': True, 'message': 'Profile marked as complete'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def error_view(request, path=None):
    """404 Error page"""
    return render(request, 'pages/error.html', {
        'error_code': '404',
        'error_title': 'Page Not Found',
        'error_message': 'The page you are looking for does not exist or may have been moved.'
    })

 
