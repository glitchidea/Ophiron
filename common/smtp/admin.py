from django.contrib import admin
from .models import SMTPConfig, EmailAutomation, EmailLog


@admin.register(SMTPConfig)
class SMTPConfigAdmin(admin.ModelAdmin):
    list_display = ['host', 'port', 'from_email', 'is_active', 'last_test_success', 'last_modified_at']
    list_filter = ['is_active', 'use_tls', 'use_ssl', 'last_test_success']
    search_fields = ['host', 'from_email', 'username']
    readonly_fields = ['last_modified_at', 'created_at', 'last_test_at']
    fieldsets = (
        ('Connection', {
            'fields': ('host', 'port', 'use_tls', 'use_ssl')
        }),
        ('Authentication', {
            'fields': ('username', 'password', 'from_email', 'from_name')
        }),
        ('Status', {
            'fields': ('is_active', 'last_modified_by', 'last_modified_at', 'created_at')
        }),
        ('Test Results', {
            'fields': ('last_test_success', 'last_test_at', 'last_test_error'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmailAutomation)
class EmailAutomationAdmin(admin.ModelAdmin):
    list_display = ['name', 'automation_type', 'is_enabled', 'schedule_type', 'last_run_status', 'next_run_at']
    list_filter = ['automation_type', 'is_enabled', 'schedule_type', 'last_run_status']
    search_fields = ['name', 'recipients']
    readonly_fields = ['created_at', 'updated_at', 'last_run_at', 'next_run_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'automation_type', 'is_enabled')
        }),
        ('Schedule', {
            'fields': ('schedule_type', 'schedule_time', 'schedule_days', 'schedule_cron')
        }),
        ('Recipients', {
            'fields': ('recipients',)
        }),
        ('Configuration', {
            'fields': ('config',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'last_modified_by', 'created_at', 'updated_at')
        }),
        ('Run History', {
            'fields': ('last_run_at', 'last_run_status', 'last_run_error', 'next_run_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['subject', 'recipient', 'status', 'automation', 'sent_at', 'created_at']
    list_filter = ['status', 'automation', 'created_at']
    search_fields = ['recipient', 'subject']
    readonly_fields = ['created_at', 'sent_at']
    date_hierarchy = 'created_at'

