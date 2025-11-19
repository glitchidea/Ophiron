"""
SMTP URLs
URL patterns for SMTP module
"""

from django.urls import path
from . import views

app_name = 'smtp'

urlpatterns = [
    # SMTP Configuration
    path('api/config/', views.get_smtp_config, name='get_config'),
    path('api/config/save/', views.save_smtp_config, name='save_config'),
    path('api/config/test/', views.test_smtp_connection, name='test_connection'),
    
    # Email Automations
    path('api/automations/', views.get_automations, name='get_automations'),
    path('api/automations/<int:automation_id>/', views.get_automation, name='get_automation'),
    path('api/automations/save/', views.save_automation, name='save_automation'),
    path('api/automations/<int:automation_id>/delete/', views.delete_automation, name='delete_automation'),
    path('api/automations/<int:automation_id>/run/', views.run_automation, name='run_automation'),
    
    # Email Logs
    path('api/logs/', views.get_email_logs, name='get_logs'),
]

