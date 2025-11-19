from django.contrib import admin
from .models import SystemUser, UserActivity, UserPermission, UserSession, SystemInfo


@admin.register(SystemUser)
class SystemUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'uid', 'gid', 'is_system_user', 'is_active', 'last_login', 'created_at')
    list_filter = ('is_system_user', 'is_active', 'created_at')
    search_fields = ('username', 'uid', 'gid')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('uid',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('username', 'uid', 'gid', 'is_system_user', 'is_active')
        }),
        ('System Information', {
            'fields': ('home_directory', 'shell', 'last_login')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'ip_address', 'timestamp')
    list_filter = ('activity_type', 'timestamp', 'user__is_system_user')
    search_fields = ('user__username', 'description', 'ip_address')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Activity Information', {
            'fields': ('user', 'activity_type', 'description')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'metadata')
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        })
    )


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'permission_name', 'permission_value', 'created_at')
    list_filter = ('permission_name', 'permission_value', 'created_at')
    search_fields = ('user__username', 'permission_name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('user__username', 'permission_name')


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_id', 'ip_address', 'login_time', 'last_activity', 'is_active')
    list_filter = ('is_active', 'login_time', 'last_activity')
    search_fields = ('user__username', 'session_id', 'ip_address')
    readonly_fields = ('login_time', 'last_activity')
    ordering = ('-last_activity',)


@admin.register(SystemInfo)
class SystemInfoAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'os_name', 'os_version', 'total_users', 'active_users', 'last_updated')
    readonly_fields = ('last_updated',)
    ordering = ('-last_updated',)
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False