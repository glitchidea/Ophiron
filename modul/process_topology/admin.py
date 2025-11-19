from django.contrib import admin
from .models import ProcessTopology, ProcessNode, ProcessConnection, ProcessSnapshot, ProcessEvent


@admin.register(ProcessTopology)
class ProcessTopologyAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(ProcessNode)
class ProcessNodeAdmin(admin.ModelAdmin):
    list_display = ['name', 'pid', 'status', 'user', 'cpu_percent', 'memory_percent', 'topology']
    list_filter = ['status', 'user', 'topology', 'created_at']
    search_fields = ['name', 'pid', 'user']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('topology', 'pid', 'name', 'status', 'user')
        }),
        ('Performans', {
            'fields': ('cpu_percent', 'memory_percent', 'memory_rss', 'memory_vms', 'num_threads')
        }),
        ('Sistem Bilgileri', {
            'fields': ('create_time', 'start_time', 'parent_pid', 'command_line', 'working_directory')
        }),
        ('Graph Pozisyonu', {
            'fields': ('x_position', 'y_position', 'node_size', 'node_color')
        }),
        ('Metadata', {
            'fields': ('environment', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ProcessConnection)
class ProcessConnectionAdmin(admin.ModelAdmin):
    list_display = ['source_node', 'target_node', 'connection_type', 'weight', 'topology']
    list_filter = ['connection_type', 'topology', 'created_at']
    search_fields = ['source_node__name', 'target_node__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(ProcessSnapshot)
class ProcessSnapshotAdmin(admin.ModelAdmin):
    list_display = ['snapshot_name', 'topology', 'timestamp', 'total_processes', 'running_processes']
    list_filter = ['topology', 'timestamp']
    search_fields = ['snapshot_name', 'description']
    readonly_fields = ['created_at']
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('topology', 'snapshot_name', 'description', 'timestamp')
        }),
        ('Süreç İstatistikleri', {
            'fields': ('total_processes', 'running_processes', 'sleeping_processes', 'zombie_processes')
        }),
        ('Performans Metrikleri', {
            'fields': ('total_cpu_percent', 'total_memory_percent', 'load_average_1min', 'load_average_5min', 'load_average_15min')
        }),
        ('Sistem Bilgileri', {
            'fields': ('system_info', 'created_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ProcessEvent)
class ProcessEventAdmin(admin.ModelAdmin):
    list_display = ['node', 'event_type', 'severity', 'timestamp', 'topology']
    list_filter = ['event_type', 'severity', 'topology', 'timestamp']
    search_fields = ['node__name', 'message']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('topology', 'node', 'event_type', 'severity', 'timestamp')
        }),
        ('Olay Detayları', {
            'fields': ('message', 'old_value', 'new_value')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        })
    )
