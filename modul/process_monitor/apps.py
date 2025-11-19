"""
Process Monitor App Configuration
"""

from django.apps import AppConfig


class ProcessMonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modul.process_monitor'
    verbose_name = 'Process Monitor'
    
    def ready(self):
        """App hazır olduğunda çalışır"""
        import logging
        
        # Import signals (tek admin sınırlaması)
        try:
            import modul.process_monitor.signals
            logger = logging.getLogger(__name__)
            logger.info("✓ Process Monitor signals loaded (single admin enforcement)")
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Signals yüklenemedi: {e}")

