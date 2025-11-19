"""
Plugin URLs
"""

from django.urls import path
from . import views

app_name = 'plugins'

urlpatterns = [
    path('list/', views.plugin_list_view, name='list'),
    path('settings/<str:plugin_name>/', views.plugin_settings_view, name='settings'),
    path('api/settings/<str:plugin_name>/', views.plugin_settings_api, name='settings_api'),
    path('api/settings/<str:plugin_name>/save/', views.plugin_settings_save_api, name='settings_save_api'),
    path('api/scheduler/<str:plugin_name>/tasks/', views.plugin_scheduler_tasks_api, name='scheduler_tasks_api'),
    path('api/scheduler/<str:plugin_name>/schedule/', views.plugin_scheduler_schedule_api, name='scheduler_schedule_api'),
    path('api/scheduler/<str:plugin_name>/<str:task_id>/unschedule/', views.plugin_scheduler_unschedule_api, name='scheduler_unschedule_api'),
    path('api/scheduler/<str:plugin_name>/<str:task_id>/toggle/', views.plugin_scheduler_toggle_api, name='scheduler_toggle_api'),
    
    # Plugin Import
    path('import/validate/', views.plugin_import_validate_api, name='import_validate'),
    path('import/', views.plugin_import_api, name='import'),
    
    # Plugin Permissions
    path('api/<str:plugin_name>/fix-permissions/', views.plugin_fix_permissions_api, name='fix_permissions_api'),
    
    # Plugin Delete
    path('api/<str:plugin_name>/delete/', views.plugin_delete_api, name='delete_api'),
]
