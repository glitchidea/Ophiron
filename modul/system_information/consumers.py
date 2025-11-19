"""
System Information WebSocket Consumer
Handles real-time system metrics updates via WebSocket
"""

import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache

from .cache import SystemInfoCache

logger = logging.getLogger(__name__)


class SystemInfoConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time system information updates.
    Sends cached system metrics to connected clients periodically.
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        try:
            # Check if user is authenticated
            if not self.scope['user'].is_authenticated:
                logger.warning("Unauthenticated WebSocket connection attempt")
                await self.close()
                return
            
            # Accept the connection
            await self.accept()
            
            logger.info(f"System Info WebSocket connected: {self.scope['user'].username}")
            
            # Add to system info group
            await self.channel_layer.group_add(
                'system_info_updates',
                self.channel_name
            )
            
            # Send initial data immediately
            await self.send_system_metrics()
            
            # Start periodic updates
            self.update_task = asyncio.create_task(self.periodic_updates())
            
        except Exception as e:
            logger.error(f"Error in WebSocket connect: {str(e)}")
            await self.close()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            # Cancel periodic updates
            if hasattr(self, 'update_task'):
                self.update_task.cancel()
            
            # Remove from system info group
            await self.channel_layer.group_discard(
                'system_info_updates',
                self.channel_name
            )
            
            logger.info(f"System Info WebSocket disconnected: {self.scope['user'].username}")
            
        except Exception as e:
            logger.error(f"Error in WebSocket disconnect: {str(e)}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'request_update':
                # Client requests immediate update
                await self.send_system_metrics()
            
            elif message_type == 'ping':
                # Respond to ping
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON received from WebSocket")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}")
    
    async def periodic_updates(self):
        """Send periodic system metrics updates"""
        try:
            while True:
                # Get monitoring interval from cache
                interval = await database_sync_to_async(cache.get)(
                    'system_info:monitoring_interval', 5
                )
                
                # Wait for the interval
                await asyncio.sleep(interval)
                
                # Send updated metrics
                await self.send_system_metrics()
                
        except asyncio.CancelledError:
            logger.debug("Periodic updates task cancelled")
        except Exception as e:
            logger.error(f"Error in periodic updates: {str(e)}")
    
    async def send_system_metrics(self):
        """Fetch and send system metrics to the client"""
        try:
            # Get cached metrics
            metrics = await database_sync_to_async(
                SystemInfoCache.get_all_metrics
            )()
            
            if metrics is None:
                logger.warning("No cached system metrics available, triggering update...")
                
                # Try to update cache immediately
                from .tasks import update_system_metrics
                try:
                    result = update_system_metrics()
                    if result.get('success'):
                        # Try to get metrics again
                        metrics = await database_sync_to_async(
                            SystemInfoCache.get_all_metrics
                        )()
                        
                        if metrics is None:
                            await self.send(text_data=json.dumps({
                                'type': 'error',
                                'message': 'Failed to generate system metrics'
                            }))
                            return
                    else:
                        await self.send(text_data=json.dumps({
                            'type': 'error',
                            'message': 'Failed to update system metrics'
                        }))
                        return
                except Exception as e:
                    logger.error(f"Error updating system metrics: {str(e)}")
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'No cached data available and failed to generate new data'
                    }))
                    return
            
            # Send metrics to client
            await self.send(text_data=json.dumps({
                'type': 'system_metrics',
                'data': metrics
            }))
            
            logger.debug(f"System metrics sent to {self.scope['user'].username}")
            
        except Exception as e:
            logger.error(f"Error sending system metrics: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def system_info_update(self, event):
        """
        Handle system_info_update messages from the channel layer.
        This allows broadcasting updates to all connected clients.
        """
        try:
            await self.send(text_data=json.dumps({
                'type': 'system_metrics',
                'data': event['data']
            }))
        except Exception as e:
            logger.error(f"Error broadcasting system info update: {str(e)}")

