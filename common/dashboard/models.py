"""
Dashboard Models
Gerçek sistem bilgilerini saklamak için modeller
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class SystemService(models.Model):
    """Sistem servislerinin durumunu takip eden model"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('failed', 'Failed'),
        ('activating', 'Activating'),
        ('deactivating', 'Deactivating'),
        ('unknown', 'Unknown'),
    ]
    
    CATEGORY_CHOICES = [
        ('web', 'Web Services'),
        ('database', 'Database'),
        ('system', 'System'),
        ('docker', 'Docker'),
        ('security', 'Security'),
        ('network', 'Network'),
        ('monitoring', 'Monitoring'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unknown')
    description = models.TextField(blank=True, null=True)
    is_critical = models.BooleanField(default=False)
    last_checked = models.DateTimeField(auto_now=True)
    last_status_change = models.DateTimeField(auto_now_add=True)
    uptime_percentage = models.FloatField(default=0.0)
    error_count = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'System Service'
        verbose_name_plural = 'System Services'
    
    def __str__(self):
        return f"{self.display_name} ({self.status})"
    
    def get_status_class(self):
        """CSS class for status"""
        status_classes = {
            'active': 'status-online',
            'inactive': 'status-offline',
            'failed': 'status-offline',
            'activating': 'status-warning',
            'deactivating': 'status-warning',
            'unknown': 'status-unknown',
        }
        return status_classes.get(self.status, 'status-unknown')
    
    def get_status_icon(self):
        """Icon for status"""
        status_icons = {
            'active': 'check-circle',
            'inactive': 'times-circle',
            'failed': 'exclamation-triangle',
            'activating': 'spinner',
            'deactivating': 'spinner',
            'unknown': 'question-circle',
        }
        return status_icons.get(self.status, 'question-circle')


class SystemAlert(models.Model):
    """Sistem uyarıları için model"""
    
    ALERT_TYPES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    service = models.ForeignKey(SystemService, on_delete=models.CASCADE, null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True, help_text="Additional notes about this alert")
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'System Alert'
        verbose_name_plural = 'System Alerts'
    
    def __str__(self):
        return f"{self.get_alert_type_display()}: {self.title}"
    
    def get_alert_icon(self):
        """Icon for alert type"""
        icons = {
            'info': 'info-circle',
            'warning': 'exclamation-triangle',
            'error': 'exclamation-circle',
            'critical': 'times-circle',
        }
        return icons.get(self.alert_type, 'info-circle')


class SystemActivity(models.Model):
    """Sistem aktivitelerini takip eden model"""
    
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('service_start', 'Service Start'),
        ('service_stop', 'Service Stop'),
        ('service_restart', 'Service Restart'),
        ('system_reboot', 'System Reboot'),
        ('config_change', 'Configuration Change'),
        ('security_event', 'Security Event'),
        ('backup', 'Backup'),
        ('update', 'Update'),
        ('other', 'Other'),
    ]
    
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    service = models.ForeignKey(SystemService, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'System Activity'
        verbose_name_plural = 'System Activities'
    
    def __str__(self):
        return f"{self.get_activity_type_display()}: {self.title}"
    
    def get_activity_icon(self):
        """Icon for activity type"""
        icons = {
            'login': 'sign-in-alt',
            'logout': 'sign-out-alt',
            'service_start': 'play',
            'service_stop': 'stop',
            'service_restart': 'redo',
            'system_reboot': 'power-off',
            'config_change': 'cog',
            'security_event': 'shield-alt',
            'backup': 'save',
            'update': 'sync',
            'other': 'info',
        }
        return icons.get(self.activity_type, 'info')


class DashboardSettings(models.Model):
    """Dashboard ayarları için model"""
    
    refresh_interval = models.IntegerField(default=5, help_text="Refresh interval in seconds")
    max_alerts = models.IntegerField(default=10, help_text="Maximum number of alerts to show")
    max_activities = models.IntegerField(default=10, help_text="Maximum number of activities to show")
    auto_refresh = models.BooleanField(default=True)
    show_critical_only = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Dashboard Settings'
        verbose_name_plural = 'Dashboard Settings'
    
    def __str__(self):
        return f"Dashboard Settings (Updated: {self.updated_at})"
    
    @classmethod
    def get_settings(cls):
        """Get or create dashboard settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class SystemMetrics(models.Model):
    """Sistem metriklerini saklayan model"""
    
    timestamp = models.DateTimeField(auto_now_add=True)
    cpu_usage = models.FloatField(default=0.0)
    memory_usage = models.FloatField(default=0.0)
    memory_total = models.BigIntegerField(default=0)
    memory_used = models.BigIntegerField(default=0)
    disk_usage = models.FloatField(default=0.0)
    disk_total = models.BigIntegerField(default=0)
    disk_used = models.BigIntegerField(default=0)
    network_in = models.BigIntegerField(default=0)
    network_out = models.BigIntegerField(default=0)
    temperature = models.FloatField(null=True, blank=True)
    uptime = models.BigIntegerField(default=0)
    load_average = models.FloatField(default=0.0)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'System Metrics'
        verbose_name_plural = 'System Metrics'
    
    def __str__(self):
        return f"Metrics at {self.timestamp}"
    
    @classmethod
    def get_latest(cls):
        """Get latest metrics"""
        return cls.objects.first()
    
    @classmethod
    def get_average(cls, hours=1):
        """Get average metrics for last N hours"""
        from django.utils import timezone
        from datetime import timedelta
        
        since = timezone.now() - timedelta(hours=hours)
        metrics = cls.objects.filter(timestamp__gte=since)
        
        if not metrics.exists():
            return None
        
        return {
            'cpu_usage': sum(m.cpu_usage for m in metrics) / metrics.count(),
            'memory_usage': sum(m.memory_usage for m in metrics) / metrics.count(),
            'disk_usage': sum(m.disk_usage for m in metrics) / metrics.count(),
            'load_average': sum(m.load_average for m in metrics) / metrics.count(),
        }