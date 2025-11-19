"""
Process Monitor Models
Kullanıcı ayarları ve background service yönetimi
"""

from django.db import models
from django.contrib.auth.models import User


class ProcessMonitorSettings(models.Model):
    """
    Global Process Monitor settings (Shared by all admins)
    Only 1 record should exist (singleton pattern)
    """
    # Live Mode Settings
    live_mode_enabled = models.BooleanField(
        default=False,
        help_text="Continuous background monitoring active (Shared by all admins)"
    )
    
    # Background Service Settings
    background_service_enabled = models.BooleanField(
        default=False,
        help_text="Enable background service"
    )
    
    # Monitoring Interval (For Real-Time)
    monitoring_interval = models.FloatField(
        default=1.0,
        help_text="Monitoring interval (seconds) - Between 0.5 and 10.0"
    )
    
    # Data Retention
    cache_duration = models.IntegerField(
        default=60,
        help_text="Cache duration (seconds)"
    )
    
    # Real-time Mode
    realtime_websocket_enabled = models.BooleanField(
        default=True,
        help_text="Real-time data transmission via WebSocket"
    )
    
    # Logging
    logging_enabled = models.BooleanField(
        default=False,
        help_text="Enable detailed logging for all Process Monitor operations"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Last modified by
    last_modified_by = models.CharField(max_length=150, blank=True, null=True)
    
    class Meta:
        verbose_name = "Process Monitor Settings"
        verbose_name_plural = "Process Monitor Settings"
    
    def __str__(self):
        return f"Live Mode: {self.live_mode_enabled} | Interval: {self.monitoring_interval}s"
    
    @classmethod
    def get_global_settings(cls):
        """Get global settings (singleton)"""
        settings, created = cls.objects.get_or_create(pk=1)
        if created:
            # Default values on first creation
            settings.live_mode_enabled = False
            settings.monitoring_interval = 1.0
            settings.background_service_enabled = False
            settings.realtime_websocket_enabled = True
            settings.save()
        return settings
    
    def save(self, *args, **kwargs):
        # Singleton pattern: Only ID=1 can be saved
        self.pk = 1
        super().save(*args, **kwargs)
        
    @classmethod
    def load(cls):
        """Load singleton instance"""
        return cls.get_global_settings()


class ProcessMonitorCache(models.Model):
    """
    Cache for Process Monitor data
    """
    cache_key = models.CharField(max_length=255, unique=True, db_index=True)
    cache_data = models.JSONField()
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Process Monitor Cache"
        verbose_name_plural = "Process Monitor Caches"
        indexes = [
            models.Index(fields=['cache_key', 'expires_at']),
        ]
    
    def __str__(self):
        return f"{self.cache_key} (expires: {self.expires_at})"
    
    @classmethod
    def get_cache(cls, key):
        """Get data from cache"""
        from django.utils import timezone
        try:
            cache = cls.objects.get(
                cache_key=key,
                expires_at__gt=timezone.now()
            )
            return cache.cache_data
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def set_cache(cls, key, data, duration=300):
        """Save data to cache"""
        from django.utils import timezone
        from datetime import timedelta
        
        expires_at = timezone.now() + timedelta(seconds=duration)
        cls.objects.update_or_create(
            cache_key=key,
            defaults={
                'cache_data': data,
                'expires_at': expires_at
            }
        )
    
    @classmethod
    def clear_expired(cls):
        """Clear expired caches"""
        from django.utils import timezone
        cls.objects.filter(expires_at__lt=timezone.now()).delete()
