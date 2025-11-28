"""
SMTP Models
Email configuration and automation models
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class SMTPConfig(models.Model):
    """SMTP server configuration"""
    
    host = models.CharField(max_length=255, help_text="SMTP server hostname")
    port = models.IntegerField(default=587, help_text="SMTP server port (usually 587 for TLS, 465 for SSL)")
    use_tls = models.BooleanField(default=True, help_text="Use TLS encryption")
    use_ssl = models.BooleanField(default=False, help_text="Use SSL encryption")
    username = models.CharField(max_length=255, help_text="SMTP username/email (also used as sender email)")
    password = models.CharField(max_length=255, help_text="SMTP password (encrypted)")
    from_email = models.EmailField(help_text="Default sender email address (auto-filled from username)", blank=True)
    from_name = models.CharField(max_length=255, default="Ophiron System", help_text="Default sender name")
    
    is_active = models.BooleanField(default=False, help_text="Enable SMTP server")
    last_modified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='smtp_configs_modified'
    )
    last_modified_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Test connection fields
    last_test_success = models.BooleanField(null=True, blank=True)
    last_test_at = models.DateTimeField(null=True, blank=True)
    last_test_error = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'smtp_smtpconfig'
        verbose_name = 'SMTP Configuration'
        verbose_name_plural = 'SMTP Configurations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"SMTP: {self.host}:{self.port} ({'Active' if self.is_active else 'Inactive'})"


class EmailAutomation(models.Model):
    """Email automation configuration"""
    
    AUTOMATION_TYPE_CHOICES = [
        ('cve', 'CVE Scanner'),
        ('report', 'System Report'),
        ('ip', 'IP Monitoring'),
        ('alert', 'System Alerts'),
        ('custom', 'Custom'),
    ]
    
    SCHEDULE_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom Cron'),
    ]
    
    name = models.CharField(max_length=255, help_text="Automation name")
    automation_type = models.CharField(
        max_length=50, 
        choices=AUTOMATION_TYPE_CHOICES,
        help_text="Type of automation"
    )
    
    # Schedule configuration
    is_enabled = models.BooleanField(default=False, help_text="Enable this automation")
    schedule_type = models.CharField(
        max_length=20,
        choices=SCHEDULE_TYPE_CHOICES,
        default='daily',
        help_text="Schedule frequency"
    )
    schedule_time = models.TimeField(
        default='06:00',
        help_text="Time to run (HH:MM format, e.g., 06:00 for 6 AM)"
    )
    timezone = models.CharField(
        max_length=64,
        default='UTC',
        help_text="IANA timezone identifier (e.g., Europe/Istanbul)"
    )
    schedule_days = models.CharField(
        max_length=50,
        blank=True,
        help_text="Days of week (comma-separated: 0=Monday, 6=Sunday) or 'daily' for all days"
    )
    schedule_cron = models.CharField(
        max_length=100,
        blank=True,
        help_text="Custom cron expression (e.g., '0 6 * * *' for daily at 6 AM)"
    )
    
    # Recipients
    recipients = models.JSONField(
        default=list,
        help_text="List of email addresses to send to"
    )
    
    # Configuration
    config = models.JSONField(
        default=dict,
        help_text="Automation-specific configuration"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_automations'
    )
    last_modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modified_automations'
    )
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_run_status = models.CharField(
        max_length=20,
        choices=[('success', 'Success'), ('error', 'Error'), ('skipped', 'Skipped')],
        null=True,
        blank=True
    )
    last_run_error = models.TextField(blank=True, null=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Email Automation'
        verbose_name_plural = 'Email Automations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.automation_type}) - {'Enabled' if self.is_enabled else 'Disabled'}"
    
    def get_schedule_description(self):
        """Get human-readable schedule description"""
        tz_label = f" ({self.timezone})" if self.timezone else ''
        if self.schedule_type == 'daily':
            return f"Daily at {self.schedule_time.strftime('%H:%M')}{tz_label}"
        elif self.schedule_type == 'weekly':
            days = self.schedule_days or "0"
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_list = [day_names[int(d)] for d in days.split(',') if d.isdigit()]
            return f"Weekly on {', '.join(day_list)} at {self.schedule_time.strftime('%H:%M')}{tz_label}"
        elif self.schedule_type == 'monthly':
            return f"Monthly on day {self.schedule_days} at {self.schedule_time.strftime('%H:%M')}{tz_label}"
        elif self.schedule_type == 'custom':
            return f"Custom cron: {self.schedule_cron}{tz_label}"
        return "Not scheduled"

    def compute_next_run(self, reference=None):
        """Calculate the next runtime for this automation."""
        from .scheduler import calculate_next_run  # Local import to avoid circular dependency
        return calculate_next_run(self, reference=reference)

    def update_next_run(self, reference=None, commit=True):
        """Recompute and optionally persist next_run_at."""
        next_run = self.compute_next_run(reference=reference)
        self.next_run_at = next_run
        if commit:
            self.save(update_fields=['next_run_at'])
        return next_run


class EmailLog(models.Model):
    """Email sending log"""
    
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]
    
    automation = models.ForeignKey(
        EmailAutomation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_logs'
    )
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.subject} to {self.recipient} - {self.status}"

