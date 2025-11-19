from django.db import models
from django.contrib.auth.models import User
import subprocess
import pwd
import grp
import os
import shutil
from datetime import datetime
import json
import platform
from .utils import parse_timestamp_safe, clean_timestamp_for_display, safe_strptime


class SystemUser(models.Model):
    """Model to store system user information"""
    username = models.CharField(max_length=100, unique=True)
    uid = models.IntegerField()
    gid = models.IntegerField()
    home_directory = models.CharField(max_length=500)
    shell = models.CharField(max_length=200)
    is_system_user = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_management_system_users'
        verbose_name = 'System User'
        verbose_name_plural = 'System Users'
    
    def __str__(self):
        return f"{self.username} (UID: {self.uid})"
    
    @classmethod
    def sync_system_users(cls):
        """Sync system users from /etc/passwd"""
        try:
            # Get all users from /etc/passwd
            system_usernames = set()
            with open('/etc/passwd', 'r') as f:
                users = []
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) >= 7:
                        username, _, uid, gid, gecos, home, shell = parts[:7]
                        system_usernames.add(username)  # Track existing usernames
                        
                        # Determine if user is system user
                        uid_int = int(uid)
                        is_system_user = (
                            uid_int < 1000 or  # Traditional system users
                            username in ['nobody', 'nogroup'] or  # Special system users
                            shell in ['/usr/bin/nologin', '/bin/false', '/sbin/nologin'] or  # No login shell
                            home == '/' or  # Root home directory
                            username.startswith('systemd-') or  # Systemd users
                            username.startswith('_')  # Some systems use underscore prefix
                        )
                        
                        users.append({
                            'username': username,
                            'uid': uid_int,
                            'gid': int(gid),
                            'home_directory': home,
                            'shell': shell,
                            'is_system_user': is_system_user
                        })
            
            # Remove users that no longer exist in /etc/passwd
            db_users = cls.objects.all()
            for db_user in db_users:
                if db_user.username not in system_usernames:
                    print(f"Removing deleted user from database: {db_user.username}")
                    db_user.delete()
            
            # Update or create users in database
            for user_data in users:
                user, created = cls.objects.update_or_create(
                    username=user_data['username'],
                    defaults={
                        'uid': user_data['uid'],
                        'gid': user_data['gid'],
                        'home_directory': user_data['home_directory'],
                        'shell': user_data['shell'],
                        'is_system_user': user_data['is_system_user']
                    }
                )
                if created:
                    print(f"Created system user: {user.username}")
                else:
                    print(f"Updated system user: {user.username}")
            
            return True
        except Exception as e:
            print(f"Error syncing system users: {e}")
            return False
    
    def get_group_name(self):
        """Get the primary group name for this user"""
        try:
            group = grp.getgrgid(self.gid)
            return group.gr_name
        except KeyError:
            return f"GID_{self.gid}"
    
    def get_user_info(self):
        """Get detailed user information"""
        try:
            user_info = pwd.getpwnam(self.username)
            return {
                'username': user_info.pw_name,
                'uid': user_info.pw_uid,
                'gid': user_info.pw_gid,
                'home_directory': user_info.pw_dir,
                'shell': user_info.pw_shell,
                'gecos': user_info.pw_gecos,
                'group_name': self.get_group_name()
            }
        except KeyError:
            return None
    
    def get_user_permissions(self):
        """Get comprehensive user permissions and capabilities"""
        try:
            permissions = {
                'groups': [],
                'sudo_access': False,
                'sudo_commands': [],
                'capabilities': [],
                'file_permissions': {},
                'network_permissions': {},
                'system_permissions': {},
                'special_permissions': []
            }
            
            # Get user groups
            try:
                import grp
                user_info = pwd.getpwnam(self.username)
                # Get all groups the user belongs to
                for group_name, _, gid, members in grp.getgrall():
                    if self.username in members or gid == user_info.pw_gid:
                        permissions['groups'].append({
                            'name': group_name,
                            'gid': gid,
                            'is_primary': gid == user_info.pw_gid
                        })
            except Exception as e:
                print(f"Error getting groups: {e}")
            
            # Check sudo access
            sudo_info = self._check_sudo_access()
            permissions['sudo_access'] = sudo_info['has_sudo']
            permissions['sudo_commands'] = sudo_info['commands']
            
            # Check capabilities
            permissions['capabilities'] = self._get_user_capabilities()
            
            # Check file permissions
            permissions['file_permissions'] = self._get_file_permissions()
            
            # Check network permissions
            permissions['network_permissions'] = self._get_network_permissions()
            
            # Check system permissions
            permissions['system_permissions'] = self._get_system_permissions()
            
            # Check special permissions
            permissions['special_permissions'] = self._get_special_permissions()
            
            return permissions
            
        except Exception as e:
            print(f"Error getting user permissions: {e}")
            return {
                'groups': [],
                'sudo_access': False,
                'sudo_commands': [],
                'capabilities': [],
                'file_permissions': {},
                'network_permissions': {},
                'system_permissions': {},
                'special_permissions': []
            }
    
    def _check_sudo_access(self):
        """Check if user has sudo access without using sudo command"""
        try:
            # Check if user is in sudo group instead of using sudo command
            has_sudo = False
            commands = []
            
            # Get user groups
            try:
                user_info = pwd.getpwnam(self.username)
                user_groups = []
                
                # Check all groups
                for group_name, _, gid, members in grp.getgrall():
                    if self.username in members or gid == user_info.pw_gid:
                        user_groups.append(group_name)
                
                # Check if user is in sudo or wheel group
                if 'sudo' in user_groups or 'wheel' in user_groups:
                    has_sudo = True
                    commands = ['ALL']  # Assume full sudo access if in sudo group
                
                # Check if user is root
                if user_info.pw_uid == 0:
                    has_sudo = True
                    commands = ['ALL']
                
            except KeyError:
                pass
            
            return {
                'has_sudo': has_sudo,
                'commands': commands
            }
        except Exception:
            return {'has_sudo': False, 'commands': []}
    
    def _get_user_capabilities(self):
        """Get user capabilities without using system commands"""
        try:
            # Instead of using getcap command, check for common capability files
            capabilities = []
            
            try:
                # Check user's home directory for capability files
                home_dir = pwd.getpwnam(self.username).pw_dir
                if os.path.exists(home_dir):
                    # Look for common capability indicators
                    capability_indicators = [
                        '.ssh/authorized_keys',
                        '.ssh/id_rsa',
                        '.ssh/id_ed25519',
                        '.gnupg/',
                        '.docker/',
                        '.kube/'
                    ]
                    
                    for indicator in capability_indicators:
                        indicator_path = os.path.join(home_dir, indicator)
                        if os.path.exists(indicator_path):
                            capabilities.append(f"Has {indicator}")
                
                # Check if user has any setuid programs (simplified check)
                if self.uid == 0:  # Root user
                    capabilities.append("Root privileges")
                    
            except Exception:
                pass
            
            return capabilities
        except Exception:
            return []
    
    def _get_file_permissions(self):
        """Get file permissions analysis"""
        try:
            user_info = pwd.getpwnam(self.username)
            home_dir = user_info.pw_dir
            
            permissions = {
                'home_directory': {
                    'path': home_dir,
                    'exists': os.path.exists(home_dir),
                    'readable': False,
                    'writable': False,
                    'executable': False
                },
                'important_files': {}
            }
            
            if os.path.exists(home_dir):
                # Check home directory permissions
                stat_info = os.stat(home_dir)
                permissions['home_directory']['readable'] = os.access(home_dir, os.R_OK)
                permissions['home_directory']['writable'] = os.access(home_dir, os.W_OK)
                permissions['home_directory']['executable'] = os.access(home_dir, os.X_OK)
            
            # Check important files
            important_files = [
                '/etc/passwd', '/etc/shadow', '/etc/group', '/etc/sudoers',
                '/etc/hosts', '/etc/resolv.conf', '/etc/fstab'
            ]
            
            for file_path in important_files:
                if os.path.exists(file_path):
                    permissions['important_files'][file_path] = {
                        'readable': os.access(file_path, os.R_OK),
                        'writable': os.access(file_path, os.W_OK),
                        'executable': os.access(file_path, os.X_OK)
                    }
            
            return permissions
        except Exception:
            return {}
    
    def _get_network_permissions(self):
        """Get network-related permissions without using system commands"""
        try:
            permissions = {
                'can_bind_ports': False,
                'can_use_raw_sockets': False,
                'can_use_privileged_ports': False,
                'network_interfaces': []
            }
            
            # Check if user can bind to privileged ports (< 1024)
            if self.uid == 0:  # Root user
                permissions['can_bind_ports'] = True
                permissions['can_use_raw_sockets'] = True
                permissions['can_use_privileged_ports'] = True
            
            # Check if user is in network-related groups
            try:
                user_info = pwd.getpwnam(self.username)
                user_groups = []
                
                # Get user groups
                for group_name, _, gid, members in grp.getgrall():
                    if self.username in members or gid == user_info.pw_gid:
                        user_groups.append(group_name)
                
                # Check for network-related groups
                network_groups = ['netdev', 'network', 'docker']
                for group in network_groups:
                    if group in user_groups:
                        permissions['can_bind_ports'] = True
                        break
                        
            except Exception:
                pass
            
            return permissions
        except Exception:
            return {}
    
    def _get_system_permissions(self):
        """Get system-level permissions"""
        try:
            permissions = {
                'is_root': self.uid == 0,
                'is_system_user': self.is_system_user,
                'can_modify_system': False,
                'can_install_packages': False,
                'can_modify_services': False,
                'can_access_logs': False
            }
            
            # Check if user can modify system files
            if self.uid == 0:
                permissions['can_modify_system'] = True
                permissions['can_install_packages'] = True
                permissions['can_modify_services'] = True
                permissions['can_access_logs'] = True
            else:
                # Check specific permissions
                try:
                    # Check if user can access system logs
                    log_dirs = ['/var/log', '/var/log/syslog', '/var/log/auth.log']
                    for log_dir in log_dirs:
                        if os.path.exists(log_dir) and os.access(log_dir, os.R_OK):
                            permissions['can_access_logs'] = True
                            break
                except Exception:
                    pass
            
            return permissions
        except Exception:
            return {}
    
    def _get_special_permissions(self):
        """Get special permissions and tags"""
        try:
            special_perms = []
            
            # Check if user is in special groups
            user_groups = [group['name'] for group in permissions['groups']]
            
            # Common special groups
            special_groups = {
                'wheel': 'Administrative access',
                'sudo': 'Sudo access',
                'docker': 'Docker access',
                'audio': 'Audio device access',
                'video': 'Video device access',
                'dialout': 'Serial port access',
                'plugdev': 'Device access',
                'netdev': 'Network device access',
                'lp': 'Printer access',
                'cdrom': 'CD/DVD access',
                'floppy': 'Floppy disk access',
                'tape': 'Tape drive access',
                'disk': 'Disk access',
                'input': 'Input device access',
                'kvm': 'Virtualization access',
                'libvirt': 'Libvirt access',
                'systemd-journal': 'Systemd journal access',
                'systemd-network': 'Systemd network access',
                'systemd-resolve': 'Systemd resolve access',
                'systemd-timesync': 'Systemd timesync access',
                'systemd-logind': 'Systemd logind access'
            }
            
            for group, description in special_groups.items():
                if group in user_groups:
                    special_perms.append({
                        'group': group,
                        'description': description,
                        'type': 'group_membership'
                    })
            
            # Check for special file permissions
            if self.uid == 0:
                special_perms.append({
                    'permission': 'root_access',
                    'description': 'Full system access',
                    'type': 'privilege'
                })
            
            # Check for setuid/setgid capabilities (simplified check)
            try:
                # Only check if user is root (simplified approach)
                if self.uid == 0:
                    special_perms.append({
                        'permission': 'setuid_programs',
                        'description': 'Has setuid programs',
                        'type': 'capability'
                    })
            except Exception:
                pass
            
            return special_perms
        except Exception:
            return []
    
    
    @classmethod
    def _get_system_info(cls):
        """Get system-specific information for user creation"""
        try:
            # Detect Linux distribution
            distro = platform.system().lower()
            
            # Get available shells
            shells = []
            shell_paths = ['/bin/bash', '/bin/sh', '/bin/zsh', '/bin/fish', '/usr/bin/bash', '/usr/bin/sh']
            for shell_path in shell_paths:
                if os.path.exists(shell_path):
                    shells.append(shell_path)
            
            # Get default shell
            default_shell = '/bin/bash'
            if '/bin/bash' in shells:
                default_shell = '/bin/bash'
            elif '/bin/sh' in shells:
                default_shell = '/bin/sh'
            elif shells:
                default_shell = shells[0]
            
            return {
                'distribution': distro,
                'available_shells': shells,
                'default_shell': default_shell
            }
        except Exception:
            return {
                'distribution': 'linux',
                'available_shells': ['/bin/bash', '/bin/sh'],
                'default_shell': '/bin/bash'
            }
    
    @classmethod
    def _set_user_password(cls, username, password):
        """Simulate password setting (read-only mode for production safety)"""
        try:
            # Simulate password setting (read-only mode)
            # In production, this would be handled by system administrators
            
            return {
                'success': True, 
                'message': f'Password setting simulated for {username} (read-only mode)',
                'simulation': True,
                'note': 'This is a simulation. Actual password setting requires system administrator privileges.'
            }
                
        except Exception as e:
            return {'success': False, 'error': f'Error in password simulation: {str(e)}'}
    
    @classmethod
    def delete_user(cls, username, remove_home=False, remove_files=False):
        """
        Simulate user deletion (read-only mode for production safety)
        
        Args:
            username (str): Username to delete
            remove_home (bool): Whether to remove home directory
            remove_files (bool): Whether to remove all user files
            
        Returns:
            dict: Result with success status and message
        """
        try:
            # Check if user exists in database
            try:
                user_obj = cls.objects.get(username=username)
            except cls.DoesNotExist:
                return {'success': False, 'error': f'User {username} not found in database'}
            
            # Simulate user deletion (read-only mode)
            # In production, this would be handled by system administrators
            
            # Log the activity (simulation)
            UserActivity.objects.create(
                user=user_obj,
                activity_type='user_deleted_simulation',
                description=f'User {username} deletion simulated (read-only mode)',
                metadata={
                    'deleted_by': 'system',
                    'remove_home': remove_home,
                    'remove_files': remove_files,
                    'simulation': True
                }
            )
            
            return {
                'success': True, 
                'message': f'User {username} deletion simulated (read-only mode)',
                'simulation': True,
                'note': 'This is a simulation. Actual user deletion requires system administrator privileges.'
            }
                
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    @classmethod
    def modify_user(cls, username, **kwargs):
        """
        Simulate user modification (read-only mode for production safety)
        
        Args:
            username (str): Username to modify
            **kwargs: User attributes to modify (home_dir, shell, full_name, etc.)
            
        Returns:
            dict: Result with success status and message
        """
        try:
            # Check if user exists in database
            try:
                user_obj = cls.objects.get(username=username)
            except cls.DoesNotExist:
                return {'success': False, 'error': f'User {username} not found in database'}
            
            # Simulate user modification (read-only mode)
            # In production, this would be handled by system administrators
            
            # Log the activity (simulation)
            UserActivity.objects.create(
                user=user_obj,
                activity_type='user_modified_simulation',
                description=f'User {username} modification simulated (read-only mode)',
                metadata={
                    'modified_by': 'system',
                    'changes': kwargs,
                    'simulation': True
                }
            )
            
            return {
                'success': True, 
                'message': f'User {username} modification simulated (read-only mode)',
                'simulation': True,
                'note': 'This is a simulation. Actual user modification requires system administrator privileges.'
            }
                
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}


class UserActivity(models.Model):
    """Model to track user activities"""
    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50)  # login, logout, command, etc.
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'user_management_user_activities'
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type} at {self.timestamp}"


class UserPermission(models.Model):
    """Model to manage user permissions"""
    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE, related_name='permissions')
    permission_name = models.CharField(max_length=100)
    permission_value = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_management_user_permissions'
        verbose_name = 'User Permission'
        verbose_name_plural = 'User Permissions'
        unique_together = ['user', 'permission_name']
    
    def __str__(self):
        return f"{self.user.username} - {self.permission_name}: {self.permission_value}"


class UserSession(models.Model):
    """Model to track user sessions"""
    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE, related_name='sessions')
    session_id = models.CharField(max_length=100, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_management_user_sessions'
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.username} - {self.session_id}"


class SystemInfo(models.Model):
    """Model to store system information"""
    hostname = models.CharField(max_length=100)
    os_name = models.CharField(max_length=100)
    os_version = models.CharField(max_length=100)
    kernel_version = models.CharField(max_length=100)
    architecture = models.CharField(max_length=50)
    total_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_management_system_info'
        verbose_name = 'System Information'
        verbose_name_plural = 'System Information'
    
    def __str__(self):
        return f"{self.hostname} - {self.os_name} {self.os_version}"
    
    @classmethod
    def update_system_info(cls):
        """Update system information"""
        try:
            import platform
            import socket
            
            system_info = {
                'hostname': socket.gethostname(),
                'os_name': platform.system(),
                'os_version': platform.release(),
                'kernel_version': platform.version(),
                'architecture': platform.machine(),
                'total_users': SystemUser.objects.count(),
                'active_users': SystemUser.objects.filter(is_active=True).count()
            }
            
            obj, created = cls.objects.update_or_create(
                hostname=system_info['hostname'],
                defaults=system_info
            )
            
            return obj
        except Exception as e:
            print(f"Error updating system info: {e}")
            return None