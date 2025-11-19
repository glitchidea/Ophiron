"""
WebSocket Consumer for Process Monitor
Gerçek zamanlı süreç ve bağlantı güncellemeleri için WebSocket handler
"""

import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .utils import process_monitor

logger = logging.getLogger(__name__)


class ProcessMonitorConsumer(AsyncWebsocketConsumer):
    """
    Process Monitor için WebSocket Consumer
    Her client kendi monitoring task'ına sahip
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.monitoring_task = None
        self.is_monitoring = False
        
    async def connect(self):
        """WebSocket bağlantısı kurulduğunda"""
        # Kullanıcı authentication kontrolü
        if self.scope["user"].is_anonymous:
            await self.close()
            return
            
        await self.accept()
        logger.info(f"WebSocket connected: {self.scope['user'].username}")
        
        # Monitoring task başlat
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self.monitor_loop())
        
    async def disconnect(self, close_code):
        """WebSocket bağlantısı kapandığında"""
        logger.info(f"WebSocket disconnected: {close_code}")
        
        # Monitoring task durdur
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def receive(self, text_data):
        """Client'tan mesaj geldiğinde"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'get_connections':
                # Manuel güncelleme isteği
                await self.send_connections_update()
                
            elif action == 'get_ports':
                # Port güncellemesi isteği
                await self.send_ports_update()
                
            elif action == 'set_interval':
                # İsteğe bağlı: Client interval değiştirebilir
                interval = data.get('interval', 1)
                logger.info(f"Interval changed to: {interval}s")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
    
    async def monitor_loop(self):
        """
        Ana monitoring loop
        Her 1 saniyede değişiklikleri kontrol eder
        """
        last_connections_hash = None
        last_ports_hash = None
        
        try:
            while self.is_monitoring:
                try:
                    # Bağlantıları kontrol et
                    connections_data = await self.get_connections_data()
                    connections_hash = hash(str(connections_data))
                    
                    # Sadece değişiklik varsa gönder
                    if connections_hash != last_connections_hash:
                        await self.send(text_data=json.dumps({
                            'type': 'connections_update',
                            'connections': connections_data
                        }))
                        last_connections_hash = connections_hash
                    
                    # Port verilerini kontrol et
                    ports_data = await self.get_ports_data()
                    ports_hash = hash(str(ports_data))
                    
                    # Sadece değişiklik varsa gönder
                    if ports_hash != last_ports_hash:
                        await self.send(text_data=json.dumps({
                            'type': 'ports_update',
                            'ports': ports_data
                        }))
                        last_ports_hash = ports_hash
                    
                    # 1 saniye bekle
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error in monitor loop: {str(e)}")
                    await asyncio.sleep(1)
                    
        except asyncio.CancelledError:
            logger.info("Monitor loop cancelled")
            raise
    
    @database_sync_to_async
    def get_connections_data(self):
        """Bağlantı verilerini al (sync -> async)"""
        try:
            connections = process_monitor.get_network_connections()
            return connections
        except Exception as e:
            logger.error(f"Error getting connections: {str(e)}")
            return []
    
    @database_sync_to_async
    def get_ports_data(self):
        """Port verilerini al (sync -> async)"""
        try:
            ports = process_monitor.get_most_used_ports(limit=6)
            return ports
        except Exception as e:
            logger.error(f"Error getting ports: {str(e)}")
            return []
    
    async def send_connections_update(self):
        """Bağlantı güncellemesi gönder"""
        connections_data = await self.get_connections_data()
        await self.send(text_data=json.dumps({
            'type': 'connections_update',
            'connections': connections_data
        }))
    
    async def send_ports_update(self):
        """Port güncellemesi gönder"""
        ports_data = await self.get_ports_data()
        await self.send(text_data=json.dumps({
            'type': 'ports_update',
            'ports': ports_data
        }))

