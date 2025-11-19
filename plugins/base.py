"""
Base Plugin Class
Tüm plugin'ler için temel sınıf
"""

from typing import Dict, Optional
from pathlib import Path
from .go_bridge import GoBridge
from .embedded_bridge import EmbeddedGoBridge


class BasePlugin:
    """Plugin'ler için temel sınıf"""
    
    def __init__(self, plugin_name: str, use_embedded: bool = False):
        self.name = plugin_name
        self.config = self._load_config()
        self.go_bridge = None
        self.use_embedded = use_embedded
        
        if self.config:
            if use_embedded:
                self.go_bridge = EmbeddedGoBridge(self.config)
            else:
                self.go_bridge = GoBridge(self.config)
    
    def _load_config(self) -> Optional[Dict]:
        """Plugin yapılandırmasını yükle"""
        from .registry import PluginRegistry
        registry = PluginRegistry()
        plugin_info = registry.get_plugin(self.name)
        
        if plugin_info:
            return plugin_info['config']
        return None
    
    def get_metadata(self) -> Dict:
        """Plugin metadata'sını döndür"""
        if not self.config:
            return {}
        
        return {
            'name': self.config.get('name'),
            'display_name': self.config.get('display_name', {}),
            'version': self.config.get('version'),
            'description': self.config.get('description', {}),
            'author': self.config.get('author', {}),
            'category': self.config.get('category'),
            'icon': self.config.get('icon'),
            'route': self.config.get('route'),
        }
    
    def is_enabled(self) -> bool:
        """Plugin aktif mi?"""
        from .registry import PluginRegistry
        registry = PluginRegistry()
        plugin_info = registry.get_plugin(self.name)
        
        if plugin_info:
            return plugin_info.get('enabled', True)
        return False
    
    def start_service(self):
        """Go servisini başlat"""
        if self.go_bridge:
            self.go_bridge.start_service()
    
    def stop_service(self):
        """Go servisini durdur"""
        if self.go_bridge:
            self.go_bridge.stop_service()
    
    def is_service_running(self) -> bool:
        """Go servisi çalışıyor mu?"""
        if self.go_bridge:
            return self.go_bridge.is_running()
        return False

