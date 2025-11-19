from django.db import models
from django.utils import timezone
import json

class ServiceTemplate(models.Model):
    """Model for service templates"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Template Name")
    description = models.TextField(blank=True, verbose_name="Description")
    template_content = models.TextField(verbose_name="Template Content")
    service_type = models.CharField(
        max_length=20,
        choices=[
            ('python', 'Python Application'),
            ('web', 'Web Application'),
            ('background', 'Background Service'),
            ('custom', 'Custom Service')
        ],
        default='python',
        verbose_name="Service Type"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Active")
    
    class Meta:
        verbose_name = "Service Template"
        verbose_name_plural = "Service Templates"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class ServiceLog(models.Model):
    """Model for service operation logs"""
    service_name = models.CharField(max_length=100, verbose_name="Service Name")
    action = models.CharField(
        max_length=20,
        choices=[
            ('start', 'Start'),
            ('stop', 'Stop'),
            ('restart', 'Restart'),
            ('enable', 'Enable'),
            ('disable', 'Disable'),
            ('create', 'Create'),
            ('delete', 'Delete')
        ],
        verbose_name="Action"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('error', 'Error'),
            ('warning', 'Warning')
        ],
        verbose_name="Status"
    )
    message = models.TextField(verbose_name="Message")
    details = models.JSONField(default=dict, blank=True, verbose_name="Details")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Time")
    user = models.CharField(max_length=100, blank=True, verbose_name="User")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP Address")
    
    class Meta:
        verbose_name = "Service Log"
        verbose_name_plural = "Service Logs"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.service_name} - {self.action} - {self.status}"


class ServiceMonitoringSettings(models.Model):
    """
    Service Monitoring settings (Shared by all admins)
    Only 1 record should exist (singleton pattern)
    """
    # Live Mode Settings
    live_mode_enabled = models.BooleanField(
        default=False,
        help_text="Enable live monitoring for Service Monitoring (Shared by all admins)"
    )
    
    # Monitoring Interval
    monitoring_interval = models.FloatField(
        default=2.0,
        help_text="Monitoring interval in seconds (1.0 to 30.0)"
    )
    
    # Logging Settings
    logging_enabled = models.BooleanField(
        default=True,
        help_text="Enable detailed logging for all Service Monitoring operations"
    )
    
    # Log Retention
    log_retention_days = models.IntegerField(
        default=30,
        help_text="Number of days to keep logs (0 = keep forever)"
    )
    
    # Real-time Logging
    realtime_logging = models.BooleanField(
        default=True,
        help_text="Enable real-time logging for Service operations"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Last modified by
    last_modified_by = models.CharField(max_length=150, blank=True, null=True)
    
    class Meta:
        verbose_name = "Service Monitoring Settings"
        verbose_name_plural = "Service Monitoring Settings"
    
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

class ServiceConfiguration(models.Model):
    """Service configuration settings"""
    key = models.CharField(max_length=100, unique=True, verbose_name="Key")
    value = models.TextField(verbose_name="Value")
    description = models.TextField(blank=True, verbose_name="Description")
    is_system = models.BooleanField(default=False, verbose_name="System Setting")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Service Configuration"
        verbose_name_plural = "Service Configurations"
    
    def __str__(self):
        return f"{self.key}: {self.value}"

class ServiceCategory(models.Model):
    """Service categories"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Category Name")
    description = models.TextField(blank=True, verbose_name="Description")
    color = models.CharField(max_length=7, default="#6c757d", verbose_name="Color")
    icon = models.CharField(max_length=50, default="fas fa-cog", verbose_name="Icon")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    
    class Meta:
        verbose_name = "Service Category"
        verbose_name_plural = "Service Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name