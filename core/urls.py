"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from django.views.static import serve as static_serve
from django.views.generic import RedirectView
import os
from . import views
from .handlers import custom_404_handler, custom_500_handler, custom_403_handler

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    # Favicon fallback
    path('favicon.ico', RedirectView.as_view(url='/static/images/ophiron.svg', permanent=False)),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('settings/', views.settings_view, name='settings'),
    path('security/activity-history/', views.activity_history_view, name='activity_history'),
    path('security/alert-management/', views.alert_management_view, name='alert_management'),
    
    # Process Monitor Module
    path('process-monitor/', include('modul.process_monitor.urls')),
    
    # System Information Module
    path('system-information/', include('modul.system_information.urls')),
    # System Logs Module
    path('system-logs/', include('modul.SystemLogs.urls')),
    # Docker Manager Module
    path('docker-manager/', include('modul.docker_manager.urls')),
    # Service Monitoring Module
    path('service-monitoring/', include('modul.service_monitoring.urls')),
    # Process Topology Module
    path('process-topology/', include('modul.process_topology.urls')),
    # Service Builder Module
    path('service-builder/', include('modul.service_builder.urls')),
    # User Management Module
    path('user-management/', include('modul.user_management.urls')),
    # Firewall Management Module
    path('firewall/', include('modul.firewall.urls')),
    # Package Manager Module
    path('package-manager/', include('modul.package_manager.urls')),
    # Developer Packages Module
    path('dev-packages/', include('modul.dev_packages.urls')),
    # CVE Scanner Module
    path('cve-scanner/', include('modul.cve_scanner.urls')),
    
    # Dashboard Module
    path('dashboard-api/', include('common.dashboard.urls')),
    
    # SMTP Module
    path('smtp/', include('common.smtp.urls')),
    
    # Plugin System
    path('plugins/', include('plugins.urls')),
]

# Auto-load plugin URLs - MUST be before other URL patterns to avoid conflicts
def load_plugin_urls():
    """Dynamically load plugin URLs"""
    try:
        from plugins.registry import PluginRegistry
        registry = PluginRegistry()
        registry.load_all_plugins()  # Ensure plugins are loaded
        plugin_urls = registry.get_plugin_urls()
        
        loaded_urls = []
        for url_info in plugin_urls:
            plugin_name = 'unknown'
            try:
                # Handle both old format (route, name) and new format (route, name, path)
                if len(url_info) == 3:
                    route, plugin_name, plugin_path = url_info
                elif len(url_info) == 2:
                    route, plugin_name = url_info
                    # Get path from registry
                    plugin_info = registry.get_plugin(plugin_name)
                    plugin_path = plugin_info['path'] if plugin_info else None
                else:
                    print(f"⚠ Warning: Invalid URL info format: {url_info}")
                    continue
                
                # Determine module path based on plugin location
                # If plugin is in downloader/, use plugins.downloader.{name}
                # Otherwise use plugins.{name}
                if plugin_path and 'downloader' in str(plugin_path):
                    module_path = f'plugins.downloader.{plugin_name}.urls'
                else:
                    module_path = f'plugins.{plugin_name}.urls'
                
                loaded_urls.append(
                    path(f'{route}/', include(module_path))
                )
                print(f"✓ Loaded URLs for plugin: {route} -> {module_path}")
            except ImportError as e:
                print(f"⚠ Warning: Could not load URLs for plugin {plugin_name}: {e}")
            except Exception as e:
                print(f"✗ Error loading URLs for plugin {plugin_name}: {e}")
                import traceback
                traceback.print_exc()
        
        return loaded_urls
    except Exception as e:
        import traceback
        print(f"✗ Error loading plugin system: {e}")
        traceback.print_exc()
        return []

# Load plugin URLs BEFORE other patterns
try:
    plugin_urls = load_plugin_urls()
    # Insert at the beginning to ensure plugin URLs are checked first
    urlpatterns = plugin_urls + urlpatterns
    if plugin_urls:
        print(f"✓ Loaded {len(plugin_urls)} plugin URL pattern(s)")
except Exception as e:
    import traceback
    print(f"✗ Failed to load plugin URLs: {e}")
    traceback.print_exc()

urlpatterns += [
    path('api/profile/upload/', views.profile_upload_view, name='profile_upload'),
    path('api/profile/remove/', views.profile_remove_view, name='profile_remove'),
    path('api/profile/check/<str:username>/', views.profile_check_view, name='profile_check'),
    path('api/alert/', views.alert_list_view, name='alert_list'),
    path('api/alert/export/', views.alert_export_view, name='alert_export'),
    path('api/alert/<int:alert_id>/note/', views.alert_add_note_view, name='alert_add_note'),
    path('api/password/change/', views.password_change_view, name='password_change'),
    path('api/2fa/setup/', views.two_factor_setup_view, name='two_factor_setup'),
    path('api/2fa/verify/', views.two_factor_verify_view, name='two_factor_verify'),
    path('api/2fa/disable/', views.two_factor_disable_view, name='two_factor_disable'),
    path('api/2fa/status/', views.two_factor_status_view, name='two_factor_status'),
    path('api/2fa/settings-status/', views.two_factor_settings_status_view, name='two_factor_settings_status'),
    path('login/2fa/', views.login_2fa_view, name='login_2fa'),
    path('api/2fa/verify-login/', views.two_factor_verify_login_view, name='two_factor_verify_login'),
    path('api/activity/', views.activity_list_view, name='activity_list'),
    path('api/activity/export/', views.activity_export_view, name='activity_export'),
    path('api/profile/update/', views.profile_update_view, name='profile_update'),
    path('api/email/change/', views.email_change_view, name='email_change'),
    path('api/name/change/', views.name_change_view, name='name_change'),
    path('api/language/change/', views.language_change_view, name='language_change'),
    path('api/timezone/change/', views.timezone_change_view, name='timezone_change'),
    path('api/timezone/list/', views.timezone_list_view, name='timezone_list'),
    path('profile-setup/', views.profile_setup_view, name='profile_setup'),
    path('api/profile-setup/complete/', views.profile_setup_complete_view, name='profile_setup_complete'),
    path('api/profile/complete/', views.profile_complete_view, name='profile_complete'),
    path('logout/', views.logout_view, name='logout'),
    path('error/', views.error_view, name='error'),
]

# Custom error handlers
handler404 = custom_404_handler
handler500 = custom_500_handler
handler403 = custom_403_handler

"""Static and media serving helpers.
Static is handled by WhiteNoise; MEDIA is served here to support uploads during dev/test.
Avoid catch-all patterns that can swallow media requests.
"""

# Always serve media from Django in this environment so profile images resolve
# Use explicit re_path with django.views.static.serve to work when DEBUG=False
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static('/data/', document_root=os.path.join(settings.BASE_DIR, 'data'))
