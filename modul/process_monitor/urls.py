"""
Process Monitor URL Configuration
"""

from django.urls import path
from . import views

app_name = 'process_monitor'

urlpatterns = [
    # Ana sayfa
    path('', views.process_monitor_view, name='index'),
    
    # API endpoints - Data
    path('api/connections/', views.get_connections_api, name='connections_api'),
    path('api/grouped/', views.get_grouped_processes_api, name='grouped_processes_api'),
    path('api/pid-grouped/', views.get_pid_grouped_processes_api, name='pid_grouped_processes_api'),
    path('api/interfaces/', views.get_interfaces_api, name='interfaces_api'),
    path('api/ports/', views.get_most_used_ports_api, name='most_used_ports_api'),
    path('api/port/<int:port>/', views.get_port_details_api, name='port_details_api'),
    path('api/ip-analysis/', views.get_ip_analysis_api, name='ip_analysis_api'),
    path('api/ip-details/', views.get_ip_details_api, name='ip_details_api'),
    path('api/process/<int:pid>/', views.get_process_details_api, name='process_details_api'),
    path('api/process/<int:pid>/<str:action>/', views.manage_process_api, name='manage_process_api'),
    path('api/search/', views.search_connections_api, name='search_connections_api'),
    path('api/search/download-report/', views.download_search_report, name='download_search_report'),
    
    # API endpoints - Service Management
    path('api/service/status/', views.get_service_status_api, name='service_status_api'),
    path('api/service/toggle-live-mode/', views.toggle_live_mode_api, name='toggle_live_mode_api'),
    path('api/service/update-settings/', views.update_monitoring_settings_api, name='update_settings_api'),
    path('api/service/force-update/', views.force_cache_update_api, name='force_cache_update_api'),
]

