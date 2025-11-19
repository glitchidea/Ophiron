from django.urls import path
from . import views

app_name = 'user_management'

urlpatterns = [
    # Main page
    path('', views.user_management_index, name='index'),
    
    # API endpoints
    path('api/users/', views.api_system_users, name='api_users'),
    path('api/users/<int:user_id>/permissions/', views.api_user_permissions, name='api_user_permissions'),
    path('api/users/<int:user_id>/', views.api_user_details, name='api_user_details'),
    path('api/users/<int:user_id>/<str:action>/', views.api_user_action, name='api_user_action'),
    path('api/sync/', views.api_sync_users, name='api_sync_users'),
    path('api/activities/', views.api_user_activities, name='api_activities'),
    path('api/sessions/', views.api_active_sessions, name='api_sessions'),
    path('api/system-info/', views.api_system_info, name='api_system_info'),
    path('api/stats/', views.api_user_stats, name='api_stats'),
    
    # User management endpoints
    path('api/create-user/', views.api_create_user, name='api_create_user'),
    path('api/delete-user/<str:username>/', views.api_delete_user, name='api_delete_user'),
    path('api/modify-user/<str:username>/', views.api_modify_user, name='api_modify_user'),
]
