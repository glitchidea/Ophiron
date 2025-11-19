import json
import docker
import asyncio
import subprocess
import pty
import select
import os
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class TerminalConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.container_id = self.scope['url_route']['kwargs']['container_id']
        self.container_group_name = f'terminal_{self.container_id}'
        self.process = None
        self.master_fd = None
        self.slave_fd = None
        
        # Join room group
        await self.channel_layer.group_add(
            self.container_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Start real terminal session
        await self.start_terminal_session()
    
    async def disconnect(self, close_code):
        # Clean up terminal session
        if self.process:
            self.process.terminate()
        if self.master_fd:
            os.close(self.master_fd)
        if self.slave_fd:
            os.close(self.slave_fd)
            
        # Leave room group
        await self.channel_layer.group_discard(
            self.container_group_name,
            self.channel_name
        )
    
    async def start_terminal_session(self):
        """Start real terminal session with container"""
        try:
            # Get Docker client
            client = docker.from_env()
            container = client.containers.get(self.container_id)
            
            if container.status != 'running':
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Container is not running'
                }))
                return
            
            # Start interactive shell in container
            self.process = container.exec_run(
                'bash',
                stdin=True,
                stdout=True,
                stderr=True,
                tty=True,
                socket=True
            )
            
            # Send initial prompt
            await self.send(text_data=json.dumps({
                'type': 'output',
                'data': '$ '
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Terminal connection failed: {str(e)}'
            }))
    
    async def read_from_container(self):
        """Read output from container and send to client"""
        try:
            while True:
                # Read from container stdout
                if hasattr(self.process, 'sock'):
                    data = self.process.sock.recv(1024)
                    if data:
                        await self.send(text_data=json.dumps({
                            'type': 'output',
                            'data': data.decode('utf-8', errors='ignore')
                        }))
                await asyncio.sleep(0.1)
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Read error: {str(e)}'
            }))
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'input':
                # Send input to container
                input_data = data.get('data', '')
                if self.process and hasattr(self.process, 'sock'):
                    self.process.sock.send(input_data.encode('utf-8'))
            elif message_type == 'resize':
                # Handle terminal resize
                pass
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Input error: {str(e)}'
            }))
