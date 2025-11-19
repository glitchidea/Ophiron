"""
Plugin Utilities
Tüm plugin'ler için ortak yardımcı fonksiyonlar
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from django.contrib.auth.models import User
from django.conf import settings


def get_plugin_setting(plugin_name: str, setting_key: str, user: Optional[User] = None, default: Any = None) -> Any:
    """
    Plugin ayarını güvenli bir şekilde al
    
    Args:
        plugin_name: Plugin adı
        setting_key: Ayar anahtarı
        user: Kullanıcı (opsiyonel, user-specific ayar için)
        default: Varsayılan değer
    
    Returns:
        Ayar değeri veya default
    """
    try:
        from .models import PluginSetting
        
        # Önce user-specific kontrol et
        if user:
            value = PluginSetting.get_setting(plugin_name, setting_key, user=user, default=None)
            if value:
                return value
        
        # Sonra global kontrol et
        value = PluginSetting.get_setting(plugin_name, setting_key, user=None, default=None)
        if value:
            return value
        
        # En son güncellenen ayarı kontrol et (herhangi bir user'dan)
        try:
            latest_setting = PluginSetting.objects.filter(
                plugin_name=plugin_name,
                setting_key=setting_key
            ).order_by('-updated_at').first()
            if latest_setting:
                return latest_setting.setting_value
        except:
            pass
        
        return default
    except Exception as e:
        print(f"Warning: Could not get plugin setting {plugin_name}.{setting_key}: {e}")
        return default


def set_plugin_setting(plugin_name: str, setting_key: str, value: str, user: Optional[User] = None, is_secret: bool = False) -> bool:
    """
    Plugin ayarını güvenli bir şekilde kaydet
    
    Args:
        plugin_name: Plugin adı
        setting_key: Ayar anahtarı
        value: Ayar değeri
        user: Kullanıcı (opsiyonel, user-specific ayar için)
        is_secret: Gizli ayar mı? (gelecekte şifreleme için)
    
    Returns:
        Başarılı mı?
    """
    try:
        from .models import PluginSetting
        
        # Önce global olarak kaydet (tüm kullanıcılar için)
        PluginSetting.set_setting(plugin_name, setting_key, value, user=None)
        
        # User-specific de kaydet (eğer user varsa)
        if user:
            PluginSetting.set_setting(plugin_name, setting_key, value, user=user)
        
        return True
    except Exception as e:
        print(f"Error setting plugin setting {plugin_name}.{setting_key}: {e}")
        return False


def restart_plugin_service(plugin_name: str) -> Tuple[bool, Optional[str]]:
    """
    Plugin servisini yeniden başlat
    
    Args:
        plugin_name: Plugin adı
    
    Returns:
        (başarılı mı, hata mesajı)
    """
    try:
        from .base import BasePlugin
        import time
        
        plugin = BasePlugin(plugin_name)
        if not plugin.go_bridge:
            return False, "Plugin has no Go service"
        
        # Servisi durdur
        plugin.go_bridge.stop_service()
        time.sleep(2)  # Biraz bekle
        
        # Servisi yeniden başlat
        success = plugin.go_bridge.start_service()
        if not success:
            return False, "Failed to start service"
        
        # Servisin başladığını doğrula
        time.sleep(1)
        if not plugin.go_bridge.is_running():
            return False, "Service started but health check failed"
        
        return True, None
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error restarting plugin service: {error_trace}")
        return False, str(e)


def check_plugin_config(plugin_name: str, setting_key: str = 'api_key') -> Dict[str, Any]:
    """
    Plugin yapılandırmasını kontrol et
    
    Args:
        plugin_name: Plugin adı
        setting_key: Kontrol edilecek ayar anahtarı
    
    Returns:
        Yapılandırma durumu
    """
    try:
        from .base import BasePlugin
        
        # Veritabanından kontrol et
        api_key = get_plugin_setting(plugin_name, setting_key, user=None, default='')
        
        # Go servisinden de kontrol et
        plugin = BasePlugin(plugin_name)
        go_has_key = False
        if plugin.go_bridge:
            try:
                response = plugin.go_bridge.request('GET', '/api/config', timeout=2)
                if response.status_code == 200:
                    go_data = response.json()
                    go_has_key = go_data.get('data', {}).get('api_configured', False)
            except:
                pass
        
        return {
            'configured': bool(api_key) or go_has_key,
            'stored_in_db': bool(api_key),
            'go_service_has_key': go_has_key,
        }
    except Exception as e:
        return {
            'configured': False,
            'error': str(e)
        }


def fix_plugin_file_permissions(plugin_name: str) -> Tuple[bool, Optional[str]]:
    """
    Plugin dosyalarının sahipliğini ve izinlerini düzelt
    Sudo kullanmadan, sadece kullanıcının sahip olduğu dosyaları düzeltir
    
    Args:
        plugin_name: Plugin adı
    
    Returns:
        (başarılı mı, hata mesajı)
    """
    try:
        plugins_dir = Path(settings.BASE_DIR) / 'plugins'
        plugin_dir = plugins_dir / plugin_name
        
        if not plugin_dir.exists():
            return False, f"Plugin directory not found: {plugin_dir}"
        
        # Mevcut kullanıcının UID/GID'sini al
        current_uid = os.getuid()
        current_gid = os.getgid()
        
        fixed_count = 0
        error_count = 0
        
        # Tüm dosyaları dolaş
        for root, dirs, files in os.walk(plugin_dir):
            root_path = Path(root)
            
            # Dizinleri kontrol et ve düzelt
            try:
                stat_info = root_path.stat()
                # Eğer dosya root'a aitse ve kullanıcı yazabiliyorsa, sahipliği değiştirmeyi dene
                # Ama sadece kullanıcının sahip olduğu dosyaları düzelt
                if stat_info.st_uid == current_uid:
                    # Zaten kullanıcıya ait, izinleri düzelt
                    try:
                        os.chmod(root_path, 0o755)  # rwxr-xr-x
                    except:
                        pass
                    fixed_count += 1
            except Exception as e:
                error_count += 1
            
            # Dosyaları kontrol et ve düzelt
            for file_name in files:
                file_path = root_path / file_name
                try:
                    stat_info = file_path.stat()
                    # Sadece kullanıcının sahip olduğu dosyaları düzelt
                    if stat_info.st_uid == current_uid:
                        # Binary dosyalar için executable izni ver
                        if file_path.suffix == '' or file_path.name.startswith('go/'):
                            try:
                                os.chmod(file_path, 0o755)  # rwxr-xr-x
                            except:
                                os.chmod(file_path, 0o644)  # rw-r--r--
                        else:
                            try:
                                os.chmod(file_path, 0o644)  # rw-r--r--
                            except:
                                pass
                        fixed_count += 1
                except Exception as e:
                    error_count += 1
        
        if error_count > 0:
            return True, f"Fixed {fixed_count} files, {error_count} errors (some files may require sudo)"
        return True, f"Fixed permissions for {fixed_count} files"
        
    except Exception as e:
        import traceback
        return False, f"Error fixing permissions: {str(e)}\n{traceback.format_exc()}"


def check_plugin_sudo_requirement(plugin_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Plugin'in sudo gereksinimini kontrol et
    
    Args:
        plugin_config: Plugin yapılandırması (plugin.json içeriği)
    
    Returns:
        Sudo gereksinim bilgisi
    """
    sudo_required = plugin_config.get('sudo_required', False)
    sudo_reason = plugin_config.get('sudo_reason', '')
    
    return {
        'sudo_required': sudo_required,
        'sudo_reason': sudo_reason,
        'has_sudo_reason': bool(sudo_reason)
    }

