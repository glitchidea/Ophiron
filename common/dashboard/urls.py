"""
Dashboard URLs
"""

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard ana sayfası
    path('', views.dashboard_overview, name='overview'),
    
    # API endpoints
    path('api/metrics/', views.get_system_metrics, name='metrics'),
    path('api/containers/', views.get_docker_containers, name='containers'),
    path('api/alerts/', views.get_alerts, name='alerts'),
    path('api/alerts/<int:alert_id>/resolve/', views.resolve_alert, name='resolve_alert'),
    path('api/alerts/<int:alert_id>/unresolve/', views.unresolve_alert, name='unresolve_alert'),
    path('api/alerts/statistics/', views.get_alert_statistics, name='alert_statistics'),
    path('api/activities/', views.get_activities, name='activities'),
    path('api/data/', views.get_dashboard_data, name='data'),
    path('api/smtp-status/', views.get_smtp_status, name='smtp_status'),
]
