from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import pyotp
import qrcode
import io
import base64
from django.core.files.base import ContentFile
from django.utils import timezone
import json

class TwoFactorAuth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor_auth')
    is_enabled = models.BooleanField(default=False, verbose_name="2FA Enabled")
    secret_key = models.CharField(max_length=32, blank=True, null=True, verbose_name="Secret Key")
    backup_codes = models.JSONField(default=list, blank=True, verbose_name="Backup Codes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.user.username} - 2FA'
    
    def generate_secret_key(self):
        """Generate new secret key"""
        self.secret_key = pyotp.random_base32()
        self.save()
        return self.secret_key
    
    def generate_qr_code(self):
        """Generate QR code"""
        if not self.secret_key:
            self.generate_secret_key()
        
        totp = pyotp.TOTP(self.secret_key)
        provisioning_uri = totp.provisioning_uri(
            name=self.user.username,
            issuer_name="Ophiron Security"
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to Base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_code_data = buffer.getvalue()
        qr_code_base64 = base64.b64encode(qr_code_data).decode()
        
        return qr_code_base64, provisioning_uri
    
    def verify_token(self, token):
        """Verify TOTP token"""
        if not self.secret_key:
            return False
        
        totp = pyotp.TOTP(self.secret_key)
        return totp.verify(token, valid_window=1)
    
    def generate_backup_codes(self, count=10):
        """Generate backup codes"""
        import secrets
        import string
        
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            codes.append(code)
        
        self.backup_codes = codes
        self.save()
        return codes
    
    def verify_backup_code(self, code):
        """Verify backup code"""
        if code in self.backup_codes:
            self.backup_codes.remove(code)
            self.save()
            return True
        return False

class UserActivity(models.Model):
    """User activity history model"""
    
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('2fa_enable', '2FA Enable'),
        ('2fa_disable', '2FA Disable'),
        ('2fa_verify', '2FA Verify'),
        ('profile_update', 'Profile Update'),
        ('profile_image_upload', 'Profile Image Upload'),
        ('profile_image_remove', 'Profile Image Remove'),
        ('email_change', 'Email Change'),
        ('name_change', 'Name Change'),
        ('language_change', 'Language Change'),
        ('timezone_change', 'Timezone Change'),
        ('api_key_regenerate', 'API Key Regenerate'),
        ('api_secret_change', 'API Secret Change'),
        ('system_preference_change', 'System Preference Change'),
        ('failed_login', 'Failed Login'),
        ('security_event', 'Security Event'),
    ]
    
    STATUS_CHOICES = [
        ('success', 'Successful'),
        ('failed', 'Failed'),
        ('warning', 'Warning'),
        ('info', 'Info'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES, verbose_name="Activity Type")
    title = models.CharField(max_length=200, verbose_name="Title")
    description = models.TextField(verbose_name="Description")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success', verbose_name="Status")
    user_agent = models.TextField(null=True, blank=True, verbose_name="User Agent")
    # Device/IP collection removed
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadata")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    
    class Meta:
        verbose_name = "User Activity"
        verbose_name_plural = "User Activities"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['activity_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.title}"
    
    @classmethod
    def log_activity(cls, user, activity_type, title, description, status='success', 
                    request=None, metadata=None, **kwargs):
        """Log activity"""
        # If user is None, save as system activity
        if user is None:
            # Create a special user for system activity or reuse an existing one
            from django.contrib.auth.models import User
            try:
                system_user = User.objects.get(username='system')
            except User.DoesNotExist:
                # Create if system user does not exist
                system_user = User.objects.create_user(
                    username='system',
                    email='system@ophiron.com',
                    password='system_password_never_used'
                )
            user = system_user
        
        activity_data = {
            'user': user,
            'activity_type': activity_type,
            'title': title,
            'description': description,
            'status': status,
            'metadata': metadata or {},
        }
        
        if request:
            activity_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        # Add extra info
        activity_data.update(kwargs)
        
        return cls.objects.create(**activity_data)
    
    @staticmethod
    def _get_device_info(request):
        """Get device info"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Simple device detection
        if 'Mobile' in user_agent or 'Android' in user_agent:
            return 'Mobile Device'
        elif 'Windows' in user_agent:
            return 'Windows'
        elif 'Mac' in user_agent:
            return 'Mac'
        elif 'Linux' in user_agent:
            return 'Linux'
        else:
            return 'Unknown'
    
    
    
    def get_icon_class(self):
        """Return icon class for activity type"""
        icon_map = {
            'login': 'fas fa-sign-in-alt',
            'logout': 'fas fa-sign-out-alt',
            'password_change': 'fas fa-key',
            '2fa_enable': 'fas fa-shield-alt',
            '2fa_disable': 'fas fa-shield-alt',
            '2fa_verify': 'fas fa-shield-alt',
            'profile_update': 'fas fa-user-edit',
            'profile_image_upload': 'fas fa-image',
            'profile_image_remove': 'fas fa-trash',
            'email_change': 'fas fa-envelope',
            'name_change': 'fas fa-user',
            'language_change': 'fas fa-language',
            'timezone_change': 'fas fa-clock',
            'api_key_regenerate': 'fas fa-key',
            'api_secret_change': 'fas fa-lock',
            'system_preference_change': 'fas fa-cog',
            'failed_login': 'fas fa-times',
            'security_event': 'fas fa-exclamation-triangle',
        }
        return icon_map.get(self.activity_type, 'fas fa-info-circle')
    
    def get_status_class(self):
        """Return status class"""
        status_map = {
            'success': 'success',
            'failed': 'failed',
            'warning': 'warning',
            'info': 'info',
        }
        return status_map.get(self.status, 'info')

class UserSession(models.Model):
    """User session model"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True, verbose_name="Session Key")
    user_agent = models.TextField(verbose_name="User Agent")
    device_name = models.CharField(max_length=200, verbose_name="Device Name")
    browser_name = models.CharField(max_length=100, verbose_name="Browser")
    browser_version = models.CharField(max_length=50, verbose_name="Browser Version")
    os_name = models.CharField(max_length=100, verbose_name="Operating System")
    os_version = models.CharField(max_length=50, verbose_name="OS Version")
    device_type = models.CharField(max_length=50, verbose_name="Device Type")  # desktop, mobile, tablet
    # IP/location collection removed
    is_active = models.BooleanField(default=True, verbose_name="Active")
    is_current = models.BooleanField(default=False, verbose_name="Current Session")
    last_activity = models.DateTimeField(auto_now=True, verbose_name="Last Activity")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    
    class Meta:
        verbose_name = "User Session"
        verbose_name_plural = "User Sessions"
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.device_name}"
    
    @classmethod
    def create_session(cls, user, session_key, request):
        """Create new session"""
        # Deactivate existing current sessions
        cls.objects.filter(user=user, is_current=True).update(is_current=False)
        
        # Get device info
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        device_info = cls._parse_user_agent(user_agent)
        
        local_location = ''
        real_location = None
        
        session = cls.objects.create(
            user=user,
            session_key=session_key,
            user_agent=user_agent,
            device_name=device_info['device_name'],
            browser_name=device_info['browser_name'],
            browser_version=device_info['browser_version'],
            os_name=device_info['os_name'],
            os_version=device_info['os_version'],
            device_type=device_info['device_type'],
            is_current=True
        )
        
        return session
    
    @classmethod
    def end_session(cls, session_key):
        """End session"""
        try:
            session = cls.objects.get(session_key=session_key)
            session.is_active = False
            session.is_current = False
            session.save()
            return True
        except cls.DoesNotExist:
            return False
    
    @classmethod
    def end_all_sessions(cls, user, exclude_session_key=None):
        """End all sessions for user"""
        sessions = cls.objects.filter(user=user, is_active=True)
        if exclude_session_key:
            sessions = sessions.exclude(session_key=exclude_session_key)
        
        sessions.update(is_active=False, is_current=False)
        return sessions.count()
    
    
    
    @staticmethod
    def _parse_user_agent(user_agent):
        """Parse user agent"""
        import re
        
        # Simple user agent parsing
        browser_name = 'Unknown'
        browser_version = 'Unknown'
        os_name = 'Unknown'
        os_version = 'Unknown'
        device_type = 'desktop'
        device_name = 'Unknown Device'
        
        # Browser detection
        if 'Chrome' in user_agent:
            browser_name = 'Chrome'
            match = re.search(r'Chrome/(\d+\.\d+)', user_agent)
            if match:
                browser_version = match.group(1)
        elif 'Firefox' in user_agent:
            browser_name = 'Firefox'
            match = re.search(r'Firefox/(\d+\.\d+)', user_agent)
            if match:
                browser_version = match.group(1)
        elif 'Safari' in user_agent and 'Chrome' not in user_agent:
            browser_name = 'Safari'
            match = re.search(r'Version/(\d+\.\d+)', user_agent)
            if match:
                browser_version = match.group(1)
        elif 'Edge' in user_agent:
            browser_name = 'Edge'
            match = re.search(r'Edge/(\d+\.\d+)', user_agent)
            if match:
                browser_version = match.group(1)
        
        # OS detection
        if 'Windows' in user_agent:
            os_name = 'Windows'
            if 'Windows NT 10.0' in user_agent:
                os_version = '10'
            elif 'Windows NT 6.3' in user_agent:
                os_version = '8.1'
            elif 'Windows NT 6.1' in user_agent:
                os_version = '7'
        elif 'Mac OS X' in user_agent:
            os_name = 'macOS'
            match = re.search(r'Mac OS X (\d+[._]\d+)', user_agent)
            if match:
                os_version = match.group(1).replace('_', '.')
        elif 'Linux' in user_agent:
            os_name = 'Linux'
        elif 'Android' in user_agent:
            os_name = 'Android'
            device_type = 'mobile'
            match = re.search(r'Android (\d+\.\d+)', user_agent)
            if match:
                os_version = match.group(1)
        elif 'iPhone' in user_agent or 'iPad' in user_agent:
            os_name = 'iOS'
            device_type = 'mobile' if 'iPhone' in user_agent else 'tablet'
            match = re.search(r'OS (\d+[._]\d+)', user_agent)
            if match:
                os_version = match.group(1).replace('_', '.')
        
        # Device name generation
        if device_type == 'mobile':
            if 'iPhone' in user_agent:
                device_name = 'iPhone'
            elif 'Android' in user_agent:
                device_name = 'Android Device'
            else:
                device_name = 'Mobile Device'
        elif device_type == 'tablet':
            if 'iPad' in user_agent:
                device_name = 'iPad'
            else:
                device_name = 'Tablet'
        else:
            if 'Mac' in user_agent:
                device_name = 'MacBook'
            elif 'Windows' in user_agent:
                device_name = 'Windows PC'
            else:
                device_name = 'Desktop'
        
        return {
            'device_name': device_name,
            'browser_name': browser_name,
            'browser_version': browser_version,
            'os_name': os_name,
            'os_version': os_version,
            'device_type': device_type
        }
    
    

# Create 2FA record for each new user
@receiver(post_save, sender=User)
def create_two_factor_auth(sender, instance, created, **kwargs):
    if created:
        TwoFactorAuth.objects.create(user=instance)
