"""
Plugin Registry System
Tüm plugin'leri yükler, kaydeder ve yönetir
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from django.conf import settings


class PluginRegistry:
    """Plugin kayıt ve yönetim sistemi"""
    
    _instance = None
    _plugins: Dict[str, Dict] = {}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.plugins_dir = Path(settings.BASE_DIR) / 'plugins'
            self._initialized = True
    
    def load_all_plugins(self) -> Dict[str, Dict]:
        """Tüm plugin'leri yükle (hem plugins/ hem de plugins/downloader/)"""
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            return {}
        
        # 1. Ana plugins/ dizinindeki plugin'leri yükle
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('_') and plugin_dir.name != 'downloader':
                plugin_json = plugin_dir / 'plugin.json'
                if plugin_json.exists():
                    try:
                        self.load_plugin(plugin_dir)
                    except Exception as e:
                        print(f"Error loading plugin {plugin_dir.name}: {e}")
        
        # 2. plugins/downloader/ dizinindeki plugin'leri yükle
        downloader_dir = self.plugins_dir / 'downloader'
        if downloader_dir.exists() and downloader_dir.is_dir():
            for plugin_dir in downloader_dir.iterdir():
                if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
                    plugin_json = plugin_dir / 'plugin.json'
                    if plugin_json.exists():
                        try:
                            self.load_plugin(plugin_dir)
                        except Exception as e:
                            print(f"Error loading plugin {plugin_dir.name}: {e}")
        
        return self._plugins
    
    def load_plugin(self, plugin_path: Path) -> Optional[Dict]:
        """Tek bir plugin yükle"""
        plugin_json = plugin_path / 'plugin.json'
        
        if not plugin_json.exists():
            return None
        
        try:
            with open(plugin_json, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            plugin_name = config.get('name')
            if not plugin_name:
                return None
            
            # Plugin bilgilerini kaydet
            self._plugins[plugin_name] = {
                'config': config,
                'path': plugin_path,
                'enabled': True,
                'loaded_at': None,
            }
            
            return self._plugins[plugin_name]
        except Exception as e:
            print(f"Error loading plugin from {plugin_path}: {e}")
            return None
    
    def get_plugin(self, name: str) -> Optional[Dict]:
        """Plugin bilgisini döndür"""
        return self._plugins.get(name)
    
    def get_all_plugins(self) -> List[Dict]:
        """Tüm plugin'leri döndür"""
        return list(self._plugins.values())
    
    def get_enabled_plugins(self) -> List[Dict]:
        """Sadece aktif plugin'leri döndür"""
        return [p for p in self._plugins.values() if p.get('enabled', True)]
    
    def register_plugin(self, plugin_path: Path) -> bool:
        """Yeni plugin kaydet"""
        try:
            plugin_info = self.load_plugin(plugin_path)
            return plugin_info is not None
        except Exception as e:
            print(f"Error registering plugin: {e}")
            return False
    
    def unregister_plugin(self, name: str) -> bool:
        """Plugin kaydını kaldır"""
        if name in self._plugins:
            del self._plugins[name]
            return True
        return False
    
    def enable_plugin(self, name: str) -> bool:
        """Plugin'i etkinleştir"""
        if name in self._plugins:
            self._plugins[name]['enabled'] = True
            return True
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """Plugin'i devre dışı bırak"""
        if name in self._plugins:
            self._plugins[name]['enabled'] = False
            return True
        return False
    
    def get_plugin_urls(self) -> List[tuple]:
        """Tüm plugin'lerin URL pattern'lerini döndür"""
        urls = []
        for plugin_info in self.get_enabled_plugins():
            config = plugin_info['config']
            route = config.get('route')
            plugin_name = config.get('name')
            
            if route and plugin_name:
                try:
                    # Plugin'in urls.py dosyasını kontrol et
                    plugin_path = plugin_info['path']
                    urls_py = plugin_path / 'urls.py'
                    
                    if urls_py.exists():
                        urls.append((route, plugin_name, plugin_path))
                except Exception as e:
                    print(f"Error getting URLs for plugin {plugin_name}: {e}")
        
        return urls

