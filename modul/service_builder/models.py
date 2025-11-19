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
    action = models.CharField(max_length=50, verbose_name="Action")
    status = models.CharField(max_length=20, verbose_name="Status")
    message = models.TextField(verbose_name="Message")
    user = models.CharField(max_length=100, default='Anonymous', verbose_name="User")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    details = models.JSONField(null=True, blank=True, verbose_name="Details")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Service Log"
        verbose_name_plural = "Service Logs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.service_name} - {self.action} ({self.status})"


class ServiceConfiguration(models.Model):
    """Model for service configurations"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Service Name")
    description = models.TextField(blank=True, verbose_name="Description")
    service_type = models.CharField(max_length=20, verbose_name="Service Type")
    application_path = models.CharField(max_length=500, verbose_name="Application Path")
    interpreter = models.CharField(max_length=200, blank=True, verbose_name="Interpreter")
    user = models.CharField(max_length=100, verbose_name="User")
    working_directory = models.CharField(max_length=500, blank=True, verbose_name="Working Directory")
    port = models.IntegerField(null=True, blank=True, verbose_name="Port")
    host = models.CharField(max_length=100, default='0.0.0.0', verbose_name="Host")
    restart_policy = models.CharField(max_length=20, default='always', verbose_name="Restart Policy")
    environment_vars = models.TextField(blank=True, verbose_name="Environment Variables")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Service Configuration"
        verbose_name_plural = "Service Configurations"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_environment_vars_dict(self):
        """Convert environment variables string to dictionary"""
        if not self.environment_vars:
            return {}
        
        env_dict = {}
        for line in self.environment_vars.split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                env_dict[key.strip()] = value.strip()
        return env_dict