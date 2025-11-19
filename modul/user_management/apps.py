from django.apps import AppConfig


class UserManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modul.user_management'
    verbose_name = 'User Management'
    
    def ready(self):
        """Initialize the app when Django starts"""
        try:
            # Import signal handlers
            from . import signals
        except ImportError:
            pass