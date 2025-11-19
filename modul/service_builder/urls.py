from django.urls import path
from . import views

app_name = 'service_builder'

urlpatterns = [
    # Main pages
    path('', views.index, name='index'),
    path('create/', views.create_service, name='create_service'),
    path('templates/', views.templates, name='templates'),
    path('services/', views.services, name='services'),
    path('logs/', views.logs, name='logs'),
    
    # Service management
    path('service/<str:service_name>/', views.service_detail, name='service_detail'),
    path('service/<str:service_name>/edit/', views.edit_service, name='edit_service'),
    path('service/<str:service_name>/control/<str:action>/', views.service_control, name='service_control'),
    
    # API endpoints
    path('api/validate-path/', views.api_validate_path, name='api_validate_path'),
    path('api/check-port/<int:port>/', views.api_check_port, name='api_check_port'),
    path('api/suggest-config/', views.api_suggest_config, name='api_suggest_config'),
    path('api/analyze-python/', views.api_analyze_python, name='api_analyze_python'),
    path('api/create-service/', views.api_create_service, name='api_create_service'),
    path('api/update-service/<str:service_name>/', views.api_update_service, name='api_update_service'),
    path('api/delete-service/<str:service_name>/', views.api_delete_service, name='api_delete_service'),
    path('api/service/<str:service_name>/control/<str:action>/', views.api_service_control, name='api_service_control'),
    path('api/service-status/<str:service_name>/', views.api_service_status, name='api_service_status'),
    path('api/service-logs/<str:service_name>/', views.api_service_logs, name='api_service_logs'),
    path('api/system-users/', views.api_system_users, name='api_system_users'),
    path('api/network-interfaces/', views.api_network_interfaces, name='api_network_interfaces'),
    path('api/service-managers/', views.api_service_managers, name='api_service_managers'),
]
