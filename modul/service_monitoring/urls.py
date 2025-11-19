from django.urls import path
from . import views

app_name = 'service_monitoring'

urlpatterns = [
    path('', views.service_monitoring_view, name='index'),
    path('api/services/', views.get_services_data, name='get_services'),
    path('api/control/<str:action>/<str:service_name>/', views.control_service, name='control_service'),
    path('api/delete/<str:service_name>/', views.delete_service, name='delete_service'),
    path('api/saved-services/', views.get_saved_services, name='get_saved_services'),
    path('api/saved-services/<str:service_id>/', views.delete_saved_service, name='delete_saved_service'),
    path('api/logs/<str:service_name>/', views.get_service_logs, name='get_service_logs'),
    path('api/details/<str:service_name>/', views.get_service_details, name='get_service_details'),
    path('api/live-mode/status/', views.get_live_mode_status, name='get_live_mode_status'),
    path('api/live-mode/toggle/', views.toggle_live_mode, name='toggle_live_mode'),
    path('api/force-refresh/', views.force_refresh, name='force_refresh'),
    
    # Logging API Endpoints
    path('api/logging/status/', views.get_logging_status, name='get_logging_status'),
    path('api/logging/toggle/', views.toggle_logging, name='toggle_logging'),
]
