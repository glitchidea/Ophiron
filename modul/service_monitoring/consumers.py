"""
WebSocket Consumer for Service Monitoring
Real-time service status updates via WebSocket
"""

import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .service_manager import ServiceManager

logger = logging.getLogger(__name__)


class ServiceMonitoringConsumer(AsyncWebsocketConsumer):
    """
    Service Monitoring WebSocket Consumer
    Each client has its own monitoring task
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.monitoring_task = None
        self.is_monitoring = False
        self.service_manager = ServiceManager()
        
    async def connect(self):
        """WebSocket connection established"""
        # User authentication check
        if self.scope["user"].is_anonymous:
            await self.close()
            return
            
        await self.accept()
        logger.info(f"Service Monitoring WebSocket connected: {self.scope['user'].username}")
        
        # Start monitoring task
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self.monitor_loop())
        
    async def disconnect(self, close_code):
        """WebSocket connection closed"""
        logger.info(f"Service Monitoring WebSocket disconnected: {close_code}")
        
        # Stop monitoring task
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def receive(self, text_data):
        """Message received from client"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'get_services':
                # Manual update request
                await self.send_services_update()
                
            elif action == 'get_service_status':
                # Service status update request
                service_name = data.get('service_name')
                if service_name:
                    await self.send_service_status_update(service_name)
                
            elif action == 'set_interval':
                # Optional: Client can change interval
                interval = data.get('interval', 2)
                logger.info(f"Service monitoring interval changed to: {interval}s")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received in Service Monitoring")
        except Exception as e:
            logger.error(f"Error in Service Monitoring receive: {str(e)}")
    
    async def monitor_loop(self):
        """
        Main monitoring loop
        Checks for changes every 2 seconds
        """
        last_services_hash = None
        
        try:
            while self.is_monitoring:
                try:
                    # Check services
                    services_data = await self.get_services_data()
                    services_hash = hash(str(services_data))
                    
                    # Send only if there are changes
                    if services_hash != last_services_hash:
                        await self.send(text_data=json.dumps({
                            'type': 'services_update',
                            'services': services_data
                        }))
                        last_services_hash = services_hash
                    
                    # Wait 2 seconds
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error in Service Monitoring loop: {str(e)}")
                    await asyncio.sleep(2)
                    
        except asyncio.CancelledError:
            logger.info("Service Monitoring loop cancelled")
            raise
    
    @database_sync_to_async
    def get_services_data(self):
        """Get services data (sync -> async)"""
        try:
            services = self.service_manager.get_services()
            return services
        except Exception as e:
            logger.error(f"Error getting services: {str(e)}")
            return []
    
    async def send_services_update(self):
        """Send services update"""
        services_data = await self.get_services_data()
        await self.send(text_data=json.dumps({
            'type': 'services_update',
            'services': services_data
        }))
    
    async def send_service_status_update(self, service_name):
        """Send specific service status update"""
        try:
            # Get service details
            service_details = await self.get_service_details(service_name)
            await self.send(text_data=json.dumps({
                'type': 'service_status_update',
                'service_name': service_name,
                'details': service_details
            }))
        except Exception as e:
            logger.error(f"Error getting service status for {service_name}: {str(e)}")
    
    @database_sync_to_async
    def get_service_details(self, service_name):
        """Get service details (sync -> async)"""
        try:
            details = self.service_manager.get_service_details(service_name)
            return details
        except Exception as e:
            logger.error(f"Error getting service details for {service_name}: {str(e)}")
            return {}
