"""
System Information WebSocket Routing
Defines WebSocket URL patterns for system information
"""

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/system-information/', consumers.SystemInfoConsumer.as_asgi()),
]

