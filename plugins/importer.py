"""
Plugin Import System
Dışarıdan plugin import etme ve doğrulama sistemi
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from django.conf import settings


class PluginImporter:
    """Plugin import ve doğrulama sistemi"""
    
    def __init__(self):
        self.plugins_dir = Path(settings.BASE_DIR) / 'plugins'
        self.downloader_dir = self.plugins_dir / 'downloader'
        
        # plugins/ ve plugins/downloader/ klasörlerini oluştur
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.downloader_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_plugin(self, plugin_path: Path) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Plugin'i doğrula
        
        Returns:
            (is_valid, plugin_info, error_message)
        """
        if not plugin_path.exists():
            return False, None, "Plugin path does not exist"
        
        if not plugin_path.is_dir():
            return False, None, "Plugin path must be a directory"
        
        # plugin.json kontrolü
        plugin_json = plugin_path / 'plugin.json'
        if not plugin_json.exists():
            return False, None, "plugin.json file not found"
        
        try:
            with open(plugin_json, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            return False, None, f"Invalid JSON in plugin.json: {str(e)}"
        except Exception as e:
            return False, None, f"Error reading plugin.json: {str(e)}"
        
        # Zorunlu alanları kontrol et
        required_fields = ['name', 'version', 'display_name', 'description']
        missing_fields = [field for field in required_fields if not config.get(field)]
        
        if missing_fields:
            return False, None, f"Missing required fields in plugin.json: {', '.join(missing_fields)}"
        
        # Plugin bilgilerini hazırla
        plugin_info = {
            'name': config.get('name'),
            'display_name': config.get('display_name', {}),
            'version': config.get('version'),
            'description': config.get('description', {}),
            'author': config.get('author', {}),
            'category': config.get('category', 'other'),
            'icon': config.get('icon', 'fas fa-cube'),
            'route': config.get('route'),
            'supported_languages': config.get('supported_languages', []),
            'dependencies': config.get('dependencies', []),
            'permissions': config.get('permissions', []),
            'go_binary': config.get('go_binary'),
            'go_port': config.get('go_port'),
            'settings': config.get('settings', {}),
            'scheduled_tasks': config.get('scheduled_tasks', []),
        }
        
        return True, plugin_info, None
    
    def check_name_conflict(self, plugin_name: str) -> bool:
        """Plugin ismi çakışması var mı kontrol et"""
        from .registry import PluginRegistry
        registry = PluginRegistry()
        registry.load_all_plugins()
        
        existing_plugin = registry.get_plugin(plugin_name)
        return existing_plugin is not None
    
    def import_plugin(self, source_path: Path, plugin_name: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Plugin'i import et
        
        Args:
            source_path: Kaynak plugin klasörü
            plugin_name: Plugin adı (None ise config'den alınır)
        
        Returns:
            (success, plugin_name, error_message)
        """
        # Önce doğrula
        is_valid, plugin_info, error = self.validate_plugin(source_path)
        if not is_valid:
            return False, None, error
        
        # Plugin adını al
        if not plugin_name:
            plugin_name = plugin_info['name']
        
        # İsim çakışması kontrolü
        if self.check_name_conflict(plugin_name):
            return False, None, f"Plugin with name '{plugin_name}' already exists in the system"
        
        # Hedef klasör (downloader/ altında)
        target_path = self.downloader_dir / plugin_name
        
        # Hedef klasör zaten varsa
        if target_path.exists():
            return False, None, f"Directory '{plugin_name}' already exists in plugins/downloader folder"
        
        try:
            # Plugin'i kopyala
            shutil.copytree(source_path, target_path, dirs_exist_ok=False)
            
            # Dosya izinlerini düzelt (sudo kullanmadan)
            from .utils import fix_plugin_file_permissions
            fix_plugin_file_permissions(plugin_name)
            
            # Registry'ye kaydet
            from .registry import PluginRegistry
            registry = PluginRegistry()
            registry.load_plugin(target_path)
            
            return True, plugin_name, None
            
        except shutil.Error as e:
            return False, None, f"Error copying plugin files: {str(e)}"
        except Exception as e:
            # Hata durumunda kopyalanan dosyaları temizle
            if target_path.exists():
                try:
                    shutil.rmtree(target_path)
                except:
                    pass
            return False, None, f"Error importing plugin: {str(e)}"
    
    def get_plugin_preview(self, plugin_path: Path) -> Optional[Dict]:
        """Plugin önizleme bilgilerini al (import öncesi)"""
        is_valid, plugin_info, error = self.validate_plugin(plugin_path)
        
        if not is_valid:
            return {
                'valid': False,
                'error': error
            }
        
        # Çakışma kontrolü
        has_conflict = self.check_name_conflict(plugin_info['name'])
        
        # Sudo gereksinimini kontrol et
        from .utils import check_plugin_sudo_requirement
        sudo_info = check_plugin_sudo_requirement(plugin_info)
        
        return {
            'valid': True,
            'name': plugin_info['name'],
            'display_name': plugin_info['display_name'],
            'version': plugin_info['version'],
            'description': plugin_info['description'],
            'author': plugin_info['author'],
            'category': plugin_info['category'],
            'icon': plugin_info['icon'],
            'route': plugin_info['route'],
            'supported_languages': plugin_info['supported_languages'],
            'dependencies': plugin_info['dependencies'],
            'permissions': plugin_info['permissions'],
            'has_go_binary': bool(plugin_info.get('go_binary')),
            'has_settings': bool(plugin_info.get('settings')),
            'has_scheduled_tasks': bool(plugin_info.get('scheduled_tasks')),
            'name_conflict': has_conflict,
            'sudo_required': sudo_info.get('sudo_required', False),
            'sudo_reason': sudo_info.get('sudo_reason', ''),
            'error': None
        }

