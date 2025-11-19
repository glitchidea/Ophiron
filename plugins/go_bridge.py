"""
Go Bridge - Go servisleri ile iletişim köprüsü
Plugin'lerin Go servisleriyle iletişim kurmasını sağlar
"""

import requests
import subprocess
import os
import signal
from pathlib import Path
from typing import Optional, Dict, Any
from django.conf import settings


class GoBridge:
    """Go servisleri ile iletişim köprüsü"""
    
    def __init__(self, plugin_config: Dict):
        self.config = plugin_config
        self.port = plugin_config.get('go_port', 8081)
        self.base_url = f"http://localhost:{self.port}"
        self.binary_path = self._get_binary_path()
        self.process: Optional[subprocess.Popen] = None
    
    def _get_binary_path(self) -> Path:
        """Go binary dosyasının yolunu döndür"""
        plugin_name = self.config.get('name')
        binary_name = self.config.get('go_binary', plugin_name)
        
        plugins_dir = Path(settings.BASE_DIR) / 'plugins'
        plugin_dir = plugins_dir / plugin_name
        binary_path = plugin_dir / 'go' / binary_name
        
        return binary_path
    
    def start_service(self) -> bool:
        """Go servisini başlat"""
        if self.is_running():
            return True
        
        if not self.binary_path.exists():
            print(f"Binary not found: {self.binary_path}")
            return False
        
        try:
            # Environment variables
            env = os.environ.copy()
            env['PORT'] = str(self.port)
            
            # Plugin ayarlarından API key gibi değerleri environment'a ekle
            try:
                from .utils import get_plugin_setting  # Use the new utility function
                plugin_name = self.config.get('name')
                
                settings_config = self.config.get('settings', {})
                for key, value_config in settings_config.items():
                    if key == 'api_key':
                        # API key'i veritabanından al
                        api_key = get_plugin_setting(plugin_name, 'api_key', user=None, default='')  # Get global setting
                        if api_key:
                            env['VIRUSTOTAL_API_KEY'] = api_key
                    else:
                        env_key = f"PLUGIN_{key.upper()}"
                        setting_value = get_plugin_setting(plugin_name, key, user=None, default='')
                        if setting_value:
                            env[env_key] = setting_value
            except Exception as e:
                print(f"Warning: Could not load plugin settings: {e}")
            
            # Platform-specific process creation
            if os.name == 'posix':
                # Unix/Linux: Create new process group
                self.process = subprocess.Popen(
                    [str(self.binary_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    preexec_fn=os.setsid
                )
            else:
                # Windows: No process group
                self.process = subprocess.Popen(
                    [str(self.binary_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env
                )
            
            # Servisin başlaması için kısa bir bekleme
            import time
            time.sleep(1)
            
            if self.is_running():
                return True
            else:
                print(f"Service started but health check failed")
                return False
        except Exception as e:
            print(f"Error starting service: {e}")
            return False
    
    def stop_service(self) -> bool:
        """Go servisini durdur"""
        if self.process:
            try:
                if os.name == 'posix':
                    # Unix/Linux: Kill process group
                    try:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                        self.process.wait(timeout=5)
                    except:
                        # Fallback to direct kill
                        self.process.terminate()
                        self.process.wait(timeout=5)
                else:
                    # Windows: Direct terminate
                    self.process.terminate()
                    self.process.wait(timeout=5)
                
                self.process = None
                return True
            except Exception as e:
                print(f"Error stopping service: {e}")
                try:
                    if self.process:
                        self.process.kill()
                        self.process = None
                except:
                    pass
                return False
        return True
    
    def is_running(self) -> bool:
        """Go servisi çalışıyor mu?"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def request(self, method: str, endpoint: str, data: Optional[Dict] = None, files: Optional[Dict] = None, timeout: Optional[int] = None) -> requests.Response:
        """Go servisine HTTP isteği gönder"""
        # Servis çalışmıyorsa başlat
        if not self.is_running():
            if not self.start_service():
                raise Exception(f"Failed to start plugin service on port {self.port}")
            import time
            time.sleep(2)  # Servisin başlaması için bekle
        
        url = f"{self.base_url}{endpoint}"
        print(f"DEBUG: Making request to {url} with method {method}, port={self.port}")  # Debug log
        
        request_timeout = timeout if timeout is not None else 30
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, timeout=request_timeout)
            elif method.upper() == 'POST':
                if files:
                    response = requests.post(url, files=files, data=data, timeout=request_timeout if timeout else 60)
                else:
                    response = requests.post(url, json=data, timeout=request_timeout)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, timeout=request_timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, timeout=request_timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Could not connect to plugin service on {self.base_url}. Make sure the plugin binary is built and the service is running. Error: {e}")
        except requests.exceptions.RequestException as e:
            print(f"Request error to {url}: {e}")
            print(f"Response status: {e.response.status_code if hasattr(e, 'response') and e.response else 'N/A'}")
            raise

