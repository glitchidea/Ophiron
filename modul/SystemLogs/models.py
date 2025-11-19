from django.db import models

class SystemLogsSettings(models.Model):
    """
    System Logs settings (Shared by all admins)
    Only 1 record should exist (singleton pattern)
    """
    # Live Mode Settings
    live_mode_enabled = models.BooleanField(
        default=False,
        help_text="Enable live monitoring for Application Logs (Shared by all admins)"
    )
    
    # Monitoring Interval
    monitoring_interval = models.FloatField(
        default=5.0,
        help_text="Monitoring interval in seconds (1.0 to 30.0)"
    )
    
    # Logging Settings
    logging_enabled = models.BooleanField(
        default=True,
        help_text="Enable detailed logging for all System Logs operations"
    )
    
    # Log Retention
    log_retention_days = models.IntegerField(
        default=30,
        help_text="Number of days to keep logs (0 = keep forever)"
    )
    
    # Real-time Logging
    realtime_logging = models.BooleanField(
        default=True,
        help_text="Enable real-time logging for System Logs operations"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Last modified by
    last_modified_by = models.CharField(max_length=150, blank=True, null=True)
    
    class Meta:
        verbose_name = "System Logs Settings"
        verbose_name_plural = "System Logs Settings"
    
    def __str__(self):
        return f"Live Mode: {self.live_mode_enabled} | Logging: {self.logging_enabled}"
    
    @classmethod
    def get_global_settings(cls):
        """Get global settings (singleton)"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton)"""
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of singleton"""
        pass
