"""
WebSocket Routing for Process Monitor
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/process-monitor/$', consumers.ProcessMonitorConsumer.as_asgi()),
]

