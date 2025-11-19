from django.apps import AppConfig


class SmtpConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common.smtp'
    verbose_name = 'SMTP Email Automation'
    
    def ready(self):
        """Initialize the app when Django starts"""
        try:
            # Import signal handlers if needed
            pass
        except ImportError:
            pass

