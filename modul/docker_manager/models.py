from django.db import models
from django.utils import timezone
import json


class DockerLog(models.Model):
    """Model for Docker operation logs"""
    container_name = models.CharField(max_length=255, verbose_name="Container Name")
    container_id = models.CharField(max_length=64, blank=True, verbose_name="Container ID")
    action = models.CharField(
        max_length=20,
        choices=[
            ('start', 'Start'),
            ('stop', 'Stop'),
            ('restart', 'Restart'),
            ('pause', 'Pause'),
            ('unpause', 'Unpause'),
            ('remove', 'Remove'),
            ('create', 'Create'),
            ('pull', 'Pull'),
            ('push', 'Push'),
            ('build', 'Build'),
            ('exec', 'Execute Command'),
            ('logs', 'View Logs'),
            ('inspect', 'Inspect'),
            ('stats', 'Statistics')
        ],
        verbose_name="Action"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('error', 'Error'),
            ('warning', 'Warning'),
            ('info', 'Info')
        ],
        verbose_name="Status"
    )
    message = models.TextField(verbose_name="Message")
    command = models.TextField(blank=True, verbose_name="Command Executed")
    details = models.JSONField(default=dict, blank=True, verbose_name="Details")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Time")
    user = models.CharField(max_length=100, blank=True, verbose_name="User")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP Address")
    
    class Meta:
        verbose_name = "Docker Log"
        verbose_name_plural = "Docker Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['container_name', 'action']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.container_name} - {self.action} - {self.status}"


class DockerSettings(models.Model):
    """
    Global Docker Manager settings (Shared by all admins)
    Only 1 record should exist (singleton pattern)
    """
    # Logging Settings
    logging_enabled = models.BooleanField(
        default=True,
        help_text="Enable detailed logging for all Docker operations"
    )
    
    # Log Retention
    log_retention_days = models.IntegerField(
        default=30,
        help_text="Number of days to keep logs (0 = keep forever)"
    )
    
    # Real-time Logging
    realtime_logging = models.BooleanField(
        default=True,
        help_text="Enable real-time logging for Docker operations"
    )
    
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Last modified by
    last_modified_by = models.CharField(max_length=150, blank=True, null=True)
    
    class Meta:
        verbose_name = "Docker Settings"
        verbose_name_plural = "Docker Settings"
    
    def __str__(self):
        return f"Logging: {self.logging_enabled}"
    
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