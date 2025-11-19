from django.urls import path
from . import views

app_name = 'system_logs'

urlpatterns = [
    path('', views.system_logs_page, name='page'),
    path('analyze/', views.analyze_logs_view, name='analyze'),
    path('detailed-analysis/', views.detailed_analysis_view, name='detailed_analysis'),
    path('export/', views.export_logs_view, name='export'),
    path('filter/', views.filter_logs_view, name='filter'),
    path('critical/', views.critical_logs_view, name='critical'),
    path('recent/', views.recent_logs_summary_view, name='recent'),
    path('level/<str:level>/', views.logs_by_level_view, name='by_level'),
    # Own (application) logs - separate UI
    path('own/', views.own_logs_page, name='own_page'),
    path('own/api/', views.own_logs_api, name='own_api'),
    path('own/categories/', views.own_categories_view, name='own_categories'),
    path('own/category/<str:category>/files/', views.own_category_files_view, name='own_category_files'),
    path('own/category/<str:category>/file/<path:filename>/', views.own_file_lines_view, name='own_file_lines'),
    path('own/category/<str:category>/days/', views.own_category_days_view, name='own_category_days'),
    path('own/category/<str:category>/download/<str:day>/', views.own_download_day_view, name='own_download_day'),
    path('own/category/<str:category>/download/all/', views.own_download_all_view, name='own_download_all'),
    path('own/category/<str:category>/download/file/<path:filename>/', views.own_download_file_view, name='own_download_file'),
    path('own/live-config/', views.own_live_config_view, name='own_live_config'),
    path('own/config/get/', views.own_config_get_view, name='own_config_get'),
    path('own/config/update/', views.own_config_update_view, name='own_config_update'),
    path('own/category/<str:category>/lines/all/', views.own_all_lines_view, name='own_all_lines'),
    path('own/category/<str:category>/lines/<str:day>/', views.own_day_lines_view, name='own_day_lines'),
]

# API endpoints
urlpatterns += [
    path('api/', views.list_logs_view, name='api_list'),
]

