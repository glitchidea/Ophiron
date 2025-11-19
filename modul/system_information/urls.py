"""
System Information URL Configuration
"""

from django.urls import path
from . import views

app_name = 'system_information'

urlpatterns = [
    # Ana sayfa
    path('', views.system_information_view, name='index'),
    
    # API endpoints - Data
    path('api/metrics/', views.get_system_metrics_api, name='metrics_api'),
    path('api/cpu/', views.get_cpu_info_api, name='cpu_api'),
    path('api/memory/', views.get_memory_info_api, name='memory_api'),
    path('api/disk/', views.get_disk_info_api, name='disk_api'),
    path('api/network/', views.get_network_info_api, name='network_api'),
    
    # API endpoints - Service Management (for Settings page)
    path('api/service/status/', views.get_service_status_api, name='service_status_api'),
    path('api/service/toggle-live-mode/', views.toggle_live_mode_api, name='toggle_live_mode_api'),
    path('api/service/update-settings/', views.update_monitoring_settings_api, name='update_settings_api'),
    path('api/service/force-update/', views.force_cache_update_api, name='force_cache_update_api'),
    path('api/live-mode/status/', views.get_live_mode_status_api, name='live_mode_status_api'),
    
    # Logging API Endpoints
    path('api/logging/status/', views.get_logging_status, name='get_logging_status'),
    path('api/logging/toggle/', views.toggle_logging, name='toggle_logging'),
]
