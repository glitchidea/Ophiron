from django.urls import path
from . import views
from . import docker_pull_manager
from . import docker_hub_cache_views

app_name = 'docker_manager'

urlpatterns = [
    path('', views.index, name='index'),
    path('containers/', views.containers, name='containers'),
    path('images/', views.images, name='images'),
    path('volumes/', views.volumes, name='volumes'),
    path('hubs/', views.hubs, name='hubs'),
    
    # Docker Hub API Endpoints
    path('api/hub/search/', docker_hub_cache_views.search_cached_images, name='search_hub'),
    path('api/hub/images/', docker_hub_cache_views.get_cached_images, name='get_images'),
    path('api/hub/cache/info/', docker_hub_cache_views.get_cache_info, name='cache_info'),
    path('api/hub/cache/clear/', docker_hub_cache_views.clear_cache, name='clear_cache'),
    path('api/hub/repository/<str:namespace>/<str:name>/', views.get_repository_details, name='repository_details'),
    path('api/hub/repository/<str:namespace>/<str:name>/tags/', views.get_repository_tags, name='repository_tags'),
    path('api/hub/pull/', docker_pull_manager.pull_image_view, name='pull_image'),
    path('api/hub/pull/status/<str:image_name>/', docker_pull_manager.get_pull_status_view, name='pull_status'),
    path('api/hub/local-images/', docker_pull_manager.list_local_images_view, name='local_images'),
    path('api/hub/refresh/', views.refresh_all_data, name='refresh_all_data'),
    path('api/hub/refresh/status/', views.get_refresh_status, name='refresh_status'),
    
    # Container Detail
    path('container/<str:container_id>/', views.container_detail, name='container_detail'),
    
    # API Endpoints
    path('api/container/<str:container_id>/stop/', views.container_stop, name='container_stop'),
    path('api/container/<str:container_id>/start/', views.container_start, name='container_start'),
    path('api/container/<str:container_id>/remove/', views.container_remove, name='container_remove'),
    path('api/container/<str:container_id>/restart/', views.container_restart, name='container_restart'),
    
    # Container Detail API Endpoints
    path('api/container/<str:container_id>/logs/', views.container_logs, name='container_logs'),
    path('api/container/<str:container_id>/inspect/', views.container_inspect, name='container_inspect'),
    path('api/container/<str:container_id>/mounts/', views.container_mounts, name='container_mounts'),
    
    
    path('api/container/<str:container_id>/files/', views.container_files, name='container_files'),
    path('api/container/<str:container_id>/files/content/', views.container_files_content, name='container_files_content'),
    path('api/container/<str:container_id>/stats/', views.container_stats, name='container_stats'),
    
    # Image Detail
    path('image/<str:image_id>/', views.image_detail, name='image_detail'),
    
    # Volume Detail
    path('volume/<str:volume_name>/', views.volume_detail, name='volume_detail'),
    
    # Volume API Endpoints
    path('api/volume/<str:volume_name>/inspect/', views.volume_inspect, name='volume_inspect'),
    path('api/volume/<str:volume_name>/delete/', views.volume_delete, name='volume_delete'),
    path('api/volume/create/', views.volume_create, name='volume_create'),
    path('api/volume/prune/', views.volume_prune, name='volume_prune'),
    
    # Image API Endpoints
    path('api/image/<str:image_id>/delete/', views.image_delete, name='image_delete'),
    path('api/image/<str:image_id>/inspect/', views.image_inspect, name='image_inspect'),
    path('api/image/<str:image_id>/history/', views.image_history, name='image_history'),
    path('api/image/<str:image_id>/logs/', views.image_logs, name='image_logs'),
    path('api/image/pull/', views.image_pull, name='image_pull'),
    path('api/image/build/', views.image_build, name='image_build'),
    path('api/image/run/', views.image_run, name='image_run'),
    
    # Builds Management API Endpoints
    path('api/build/image/', views.build_image, name='build_image'),
    path('api/build/git/', views.build_from_git, name='build_from_git'),
    path('api/build/<str:build_id>/logs/', views.get_build_logs, name='get_build_logs'),
    path('api/build/<str:build_id>/delete/', views.delete_build, name='delete_build'),
    path('api/build/<str:build_id>/inspect/', views.build_inspect, name='build_inspect'),
    path('api/build/prune/', views.build_prune, name='build_prune'),
    
    # Logging API Endpoints
    path('api/logging/status/', views.get_logging_status, name='get_logging_status'),
    path('api/logging/toggle/', views.toggle_logging, name='toggle_logging'),
    
    # Docker Service API Endpoints
    path('api/service/restart/', views.docker_service_restart, name='docker_service_restart'),
]
