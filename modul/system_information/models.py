"""
System Information Models
Global settings for System Information monitoring
"""

from django.db import models
from django.contrib.auth.models import User




class SystemInformationLog(models.Model):
    """Model for System Information operation logs"""
    operation_type = models.CharField(
        max_length=30,
        choices=[
            ('system_info', 'System Information'),
            ('hardware_info', 'Hardware Information'),
            ('network_info', 'Network Information'),
            ('disk_info', 'Disk Information'),
            ('memory_info', 'Memory Information'),
            ('cpu_info', 'CPU Information'),
            ('process_info', 'Process Information'),
            ('service_info', 'Service Information'),
            ('user_info', 'User Information'),
            ('system_health', 'System Health Check'),
            ('performance_metrics', 'Performance Metrics'),
            ('security_scan', 'Security Scan'),
            ('update_check', 'Update Check'),
            ('backup_operation', 'Backup Operation'),
            ('maintenance', 'Maintenance Task')
        ],
        verbose_name="Operation Type"
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
    details = models.JSONField(default=dict, blank=True, verbose_name="Details")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Time")
    user = models.CharField(max_length=100, blank=True, verbose_name="User")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP Address")
    execution_time = models.FloatField(blank=True, null=True, verbose_name="Execution Time (seconds)")
    
    class Meta:
        verbose_name = "System Information Log"
        verbose_name_plural = "System Information Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['operation_type', 'status']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.operation_type} - {self.status}"


class SystemInformationSettings(models.Model):
    """
    Extended System Information settings with logging
    """
    # Live Mode Settings
    live_mode_enabled = models.BooleanField(
        default=False,
        help_text="Continuous background monitoring active (Shared by all admins)"
    )
    
    # Monitoring Interval (For Real-Time)
    monitoring_interval = models.FloatField(
        default=5.0,
        help_text="Monitoring interval (seconds) - Between 1.0 and 60.0"
    )
    
    # Cache Duration
    cache_duration = models.IntegerField(
        default=10,
        help_text="Cache duration (seconds)"
    )
    
    # Real-time Mode
    realtime_websocket_enabled = models.BooleanField(
        default=True,
        help_text="Real-time data transmission via WebSocket"
    )
    
    # Logging Settings
    logging_enabled = models.BooleanField(
        default=True,
        help_text="Enable detailed logging for all System Information operations"
    )
    
    # Log Retention
    log_retention_days = models.IntegerField(
        default=30,
        help_text="Number of days to keep logs (0 = keep forever)"
    )
    
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Last modified by
    last_modified_by = models.CharField(max_length=150, blank=True, null=True)
    
    class Meta:
        verbose_name = "System Information Settings"
        verbose_name_plural = "System Information Settings"
    
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
