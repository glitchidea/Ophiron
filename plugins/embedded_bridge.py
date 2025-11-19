"""
Embedded Go Bridge - PID tabanlı, port gerektirmeyen sistem
Go servisleri port açmak yerine, stdin/stdout üzerinden iletişim kurar
API key'ler her request'te header olarak gönderilir
"""

import subprocess
import os
import signal
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from django.conf import settings


class EmbeddedGoBridge:
    """Embedded Go Bridge - PID tabanlı, port gerektirmeyen"""
    
    def __init__(self, plugin_config: Dict):
        self.config = plugin_config
        self.binary_path = self._get_binary_path()
        self.process: Optional[subprocess.Popen] = None
    
    def _ensure_binary_executable(self):
        """Binary dosyasının çalıştırılabilir olduğundan emin ol"""
        if not self.binary_path.exists():
            raise FileNotFoundError(f"Binary not found: {self.binary_path}")
        
        if os.access(self.binary_path, os.X_OK):
            return
        
        try:
            current_mode = self.binary_path.stat().st_mode
            self.binary_path.chmod(current_mode | 0o111)
        except Exception as chmod_error:
            raise PermissionError(
                f"Binary is not executable and chmod failed: {chmod_error}"
            )
        
        if not os.access(self.binary_path, os.X_OK):
            raise PermissionError(
                f"Binary is not executable even after chmod: {self.binary_path}"
            )
    
    def _get_binary_path(self) -> Path:
        """Go binary dosyasının yolunu döndür"""
        plugin_name = self.config.get('name')
        binary_name = self.config.get('go_binary', plugin_name)
        
        # Önce registry'den plugin path'ini al (daha güvenilir)
        try:
            from .registry import PluginRegistry
            registry = PluginRegistry()
            plugin_info = registry.get_plugin(plugin_name)
            if plugin_info and 'path' in plugin_info:
                plugin_path = plugin_info['path']
                binary_path = plugin_path / 'go' / binary_name
                if binary_path.exists():
                    return binary_path
        except Exception as e:
            print(f"Warning: Could not get plugin path from registry: {e}")
        
        # Fallback: Manuel arama
        plugins_dir = Path(settings.BASE_DIR) / 'plugins'
        
        # Önce downloader klasöründe ara
        downloader_plugin_dir = plugins_dir / 'downloader' / plugin_name
        downloader_binary_path = downloader_plugin_dir / 'go' / binary_name
        
        if downloader_binary_path.exists():
            return downloader_binary_path
        
        # Sonra ana plugins klasöründe ara
        plugin_dir = plugins_dir / plugin_name
        binary_path = plugin_dir / 'go' / binary_name
        
        return binary_path
    
    def start_service(self) -> bool:
        """Go servisini başlat (stdin/stdout mode)"""
        if self.is_running():
            print(f"DEBUG: Service already running (PID: {self.process.pid if self.process else 'N/A'})")
            return True
        
        try:
            self._ensure_binary_executable()
        except Exception as e:
            print(f"ERROR: {e}")
            return False
        
        print(f"DEBUG: Starting service from binary: {self.binary_path}")
        
        try:
            # Environment variables - port yok, embedded mode
            env = os.environ.copy()
            env['MODE'] = 'embedded'  # Embedded mode flag
            
            # Platform-specific process creation
            if os.name == 'posix':
                # Unix/Linux: Create new process group, stdin/stdout pipe
                self.process = subprocess.Popen(
                    [str(self.binary_path)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    preexec_fn=os.setsid,
                    text=True,
                    bufsize=1
                )
            else:
                # Windows: No process group
                self.process = subprocess.Popen(
                    [str(self.binary_path)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True,
                    bufsize=1
                )
            
            # Process PID'sini kontrol et
            if self.process and self.process.pid:
                print(f"DEBUG: Service started with PID: {self.process.pid}")
            else:
                print(f"ERROR: Process started but PID is None")
                return False
            
            # Servisin başlaması için kısa bir bekleme
            import time
            time.sleep(0.5)
            
            # Process hala çalışıyor mu kontrol et
            if self.process.poll() is None:  # None = hala çalışıyor
                print(f"DEBUG: Service is running (PID: {self.process.pid})")
                return True
            else:
                # Process öldü, stderr'i oku
                try:
                    stderr_output = self.process.stderr.read()
                    print(f"ERROR: Service process died immediately. stderr: {stderr_output}")
                except:
                    pass
                return False
        except Exception as e:
            print(f"ERROR: Exception starting service: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop_service(self) -> bool:
        """Go servisini durdur (process objesi üzerinden)"""
        if self.process:
            try:
                pid = self.process.pid
                if os.name == 'posix':
                    # Unix/Linux: Kill process group
                    try:
                        os.killpg(os.getpgid(pid), signal.SIGTERM)
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
            except Exception as e:
                print(f"Error stopping process: {e}")
                try:
                    if self.process:
                        self.process.kill()
                        self.process = None
                except:
                    pass
        
        return True
    
    def is_running(self) -> bool:
        """Go servisi çalışıyor mu? (process objesi üzerinden kontrol)"""
        if self.process:
            if self.process.poll() is None:  # Process hala çalışıyor
                return True
            else:
                # Process öldü, temizle
                print(f"DEBUG: Process object exists but process is dead (exit code: {self.process.poll()})")
                self.process = None
        
        return False
    
    def request(self, method: str, endpoint: str, data: Optional[Dict] = None, api_key: Optional[str] = None, settings: Optional[Dict] = None, timeout: Optional[int] = None):
        """Go servisine istek gönder (stdin/stdout üzerinden) - Ephemeral process"""
        # Her request için yeni bir ephemeral process başlat
        # İşlem bitince process otomatik kapanacak
        
        process = None
        try:
            self._ensure_binary_executable()
            
            # Environment variables - embedded mode
            env = os.environ.copy()
            env['MODE'] = 'embedded'
            
            # Add Django venv Python path if available
            # Try to find venv Python from BASE_DIR or sys.executable
            python_path = None
            
            # First try: Django settings BASE_DIR
            try:
                if hasattr(settings, 'BASE_DIR') and settings.BASE_DIR:
                    base_dir = Path(settings.BASE_DIR)
                    venv_python = base_dir / 'venv' / 'bin' / 'python3'
                    if venv_python.exists():
                        python_path = str(venv_python)
            except Exception:
                pass
            
            # Second try: sys.executable (current Python interpreter)
            if not python_path:
                import sys
                if sys.executable:
                    python_path = sys.executable
            
            # Third try: Common venv paths
            if not python_path:
                common_paths = [
                    Path(__file__).parent.parent.parent / 'venv' / 'bin' / 'python3',
                    Path('/home/jonh/Desktop/ophiron/venv/bin/python3'),
                ]
                for path in common_paths:
                    if path.exists():
                        python_path = str(path)
                        break
            
            # Set environment variables if Python path found
            if python_path:
                env['PYTHON_PATH'] = python_path
                env['VENV_PYTHON'] = python_path
            
            print(f"DEBUG: Starting ephemeral process for request: {endpoint}")
            
            # Yeni process başlat (sadece bu request için)
            if os.name == 'posix':
                process = subprocess.Popen(
                    [str(self.binary_path)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    preexec_fn=os.setsid,
                    text=True,
                    bufsize=1
                )
            else:
                process = subprocess.Popen(
                    [str(self.binary_path)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True,
                    bufsize=1
                )
            
            if not process or not process.pid:
                raise Exception("Failed to start ephemeral process")
            
            print(f"DEBUG: Ephemeral process started (PID: {process.pid})")
            
            # Process'in hazır olması için kısa bekleme
            import time
            time.sleep(0.2)
            
            # Process öldü mü kontrol et
            if process.poll() is not None:
                stderr_output = process.stderr.read() if process.stderr else "No stderr"
                raise Exception(f"Process died immediately. stderr: {stderr_output}")
        
        except Exception as e:
            if process:
                try:
                    process.terminate()
                    process.wait(timeout=2)
                except:
                    try:
                        process.kill()
                    except:
                        pass
            raise Exception(f"Failed to start ephemeral process: {e}")
        
        try:
            # Request'i JSON olarak hazırla
            request_data = {
                'method': method.upper(),
                'endpoint': endpoint,
                'data': data or {},
                'api_key': api_key,  # API key'i request içinde gönder
            }
            
            # Settings varsa ekle (SMTP config gibi)
            if settings:
                request_data['settings'] = settings
            
            request_json = json.dumps(request_data) + '\n'
            
            # Request'i stdin'e yaz
            process.stdin.write(request_json)
            process.stdin.flush()
            
            # Response'u stdout'tan oku (timeout ile)
            import select
            import threading
            
            response_line = None
            read_error = None
            
            def read_response():
                nonlocal response_line, read_error
                try:
                    print(f"DEBUG: Reading response from stdout...")
                    response_line = process.stdout.readline()
                    print(f"DEBUG: Read line from stdout: {response_line[:200] if response_line else 'None'}...")
                except Exception as e:
                    read_error = e
                    print(f"ERROR: Exception reading stdout: {e}")
            
            # Thread ile oku (timeout için)
            print(f"DEBUG: Starting read thread with timeout: {timeout or 30} seconds")
            read_thread = threading.Thread(target=read_response)
            read_thread.daemon = True
            read_thread.start()
            read_thread.join(timeout=timeout or 30)
            
            if read_thread.is_alive():
                print(f"WARNING: Read thread still alive after timeout")
            else:
                print(f"DEBUG: Read thread completed")
            
            # Stderr'i oku (hata mesajları için) - real-time
            stderr_output = ""
            stderr_lines = []
            if process.stderr:
                try:
                    # Read stderr in real-time while waiting for response
                    import select
                    if os.name == 'posix':
                        # Read available stderr data
                        while True:
                            ready, _, _ = select.select([process.stderr], [], [], 0.1)
                            if ready:
                                line = process.stderr.readline()
                                if line:
                                    stderr_lines.append(line)
                                    print(f"DEBUG: Go stderr: {line.rstrip()}")
                                else:
                                    break
                            else:
                                # No more data available
                                break
                        stderr_output = ''.join(stderr_lines)
                except Exception as stderr_err:
                    print(f"WARNING: Error reading stderr: {stderr_err}")
                    pass
            
            if stderr_output:
                print(f"DEBUG: Total Go process stderr output: {len(stderr_output)} chars")
            
            if read_thread.is_alive():
                # Timeout - process'i öldür
                print(f"ERROR: Request timeout after {timeout or 30} seconds")
                print(f"ERROR: Process still running: {process.poll() is None}")
                try:
                    # Read remaining stderr
                    if process.stderr:
                        remaining_stderr = ""
                        try:
                            if os.name == 'posix':
                                if select.select([process.stderr], [], [], 0.1)[0]:
                                    remaining_stderr = process.stderr.read()
                        except:
                            pass
                        if remaining_stderr:
                            print(f"ERROR: Remaining stderr: {remaining_stderr}")
                    
                    process.terminate()
                    process.wait(timeout=2)
                except:
                    try:
                        process.kill()
                    except:
                        pass
                error_msg = f"Request timeout after {timeout or 30} seconds"
                if stderr_output:
                    error_msg += f". stderr: {stderr_output}"
                raise Exception(error_msg)
            
            if read_error:
                error_msg = f"Error reading response: {read_error}"
                if stderr_output:
                    error_msg += f". stderr: {stderr_output}"
                print(f"ERROR: {error_msg}")
                raise Exception(error_msg)
            
            if not response_line:
                error_msg = "No response from plugin service"
                if stderr_output:
                    error_msg += f". stderr: {stderr_output}"
                print(f"ERROR: {error_msg}")
                raise Exception(error_msg)
            
            print(f"DEBUG: Response line received, length: {len(response_line)}")
            
            # JSON parse et
            print(f"DEBUG: Parsing JSON response...")
            try:
                response = json.loads(response_line.strip())
                print(f"DEBUG: JSON parsed successfully, status: {response.get('status', 'N/A')}")
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON response: {e}. Response: {response_line[:200]}"
                if stderr_output:
                    error_msg += f". stderr: {stderr_output}"
                print(f"ERROR: {error_msg}")
                raise Exception(error_msg)
            
            # Mock requests.Response benzeri bir obje oluştur
            class MockResponse:
                def __init__(self, data):
                    self.data = data
                    self.status_code = data.get('status') == 'ok' and 200 or 500
                    self._json = data
                
                def json(self):
                    return self._json
                
                def raise_for_status(self):
                    if self.status_code >= 400:
                        raise Exception(f"HTTP {self.status_code}: {self.data.get('message', 'Error')}")
            
            return MockResponse(response)
            
        except Exception as e:
            # Process'i temizle
            if process:
                try:
                    process.terminate()
                    process.wait(timeout=1)
                except:
                    try:
                        process.kill()
                    except:
                        pass
            print(f"Error in embedded request: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to communicate with plugin service: {e}")
        
        finally:
            # Process'i kapat (ephemeral - işlem bitince kapanır)
            if process:
                try:
                    print(f"DEBUG: Closing ephemeral process (PID: {process.pid})")
                    # Stdin'i kapat (process'in exit olmasını sağla)
                    try:
                        process.stdin.close()
                    except:
                        pass
                    
                    # Process'in kapanmasını bekle (max 2 saniye)
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        # Zorla kapat
                        try:
                            if os.name == 'posix':
                                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                            else:
                                process.terminate()
                            process.wait(timeout=1)
                        except:
                            try:
                                process.kill()
                            except:
                                pass
                except Exception as e:
                    print(f"Warning: Error closing process: {e}")

