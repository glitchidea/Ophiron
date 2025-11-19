"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Initialize Django ASGI application early to ensure AppRegistry is populated
django_asgi_app = get_asgi_application()

# Import routing after Django is initialized
from modul.process_monitor.routing import websocket_urlpatterns as process_monitor_ws
from modul.system_information.routing import websocket_urlpatterns as system_info_ws
from modul.docker_manager.routing import websocket_urlpatterns as docker_manager_ws
from modul.service_monitoring.routing import websocket_urlpatterns as service_monitoring_ws

# Combine all WebSocket URL patterns
websocket_urlpatterns = process_monitor_ws + system_info_ws + docker_manager_ws + service_monitoring_ws

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
