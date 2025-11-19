"""
Plugin i18n System - Modüler ve güvenli plugin çeviri sistemi
"""

import json
from pathlib import Path
from typing import Dict, Optional, Any
from django.conf import settings
from django.utils import translation
from django.utils.safestring import mark_safe


class PluginI18n:
    """Plugin çeviri yönetim sistemi"""
    
    _cache: Dict[str, Dict[str, Dict[str, str]]] = {}
    _initialized: Dict[str, bool] = {}
    
    @classmethod
    def get_plugin_translation(cls, plugin_name: str, key: str, default: Optional[str] = None, 
                               language: Optional[str] = None) -> str:
        """
        Plugin çevirisini al
        
        Args:
            plugin_name: Plugin adı
            key: Çeviri anahtarı (örn: "display_name", "description")
            default: Varsayılan değer
            language: Dil kodu (None ise sistem dili kullanılır)
        
        Returns:
            Çevrilmiş metin
        """
        if language is None:
            language = translation.get_language() or settings.LANGUAGE_CODE
        
        # Dil kodunu normalize et (tr-tr -> tr)
        language = language.split('-')[0].lower()
        
        # Cache'den kontrol et
        cache_key = f"{plugin_name}_{language}"
        if cache_key in cls._cache:
            translations = cls._cache[cache_key]
            if key in translations:
                return translations[key]
        
        # Plugin config'den çeviriyi al
        try:
            from .registry import PluginRegistry
            registry = PluginRegistry()
            plugin_info = registry.get_plugin(plugin_name)
            
            if not plugin_info:
                return default or key
            
            config = plugin_info.get('config', {})
            
            # Önce plugin.json'dan çeviriyi al
            translation_value = cls._get_from_config(config, key, language)
            
            if translation_value:
                # Cache'e kaydet
                if cache_key not in cls._cache:
                    cls._cache[cache_key] = {}
                cls._cache[cache_key][key] = translation_value
                return translation_value
            
            # Locale dosyasından çeviriyi al
            translation_value = cls._get_from_locale(plugin_name, key, language)
            
            if translation_value:
                # Cache'e kaydet
                if cache_key not in cls._cache:
                    cls._cache[cache_key] = {}
                cls._cache[cache_key][key] = translation_value
                return translation_value
            
            # Fallback: default dil (genellikle 'en')
            if language != 'en':
                translation_value = cls._get_from_config(config, key, 'en')
                if translation_value:
                    return translation_value
                
                translation_value = cls._get_from_locale(plugin_name, key, 'en')
                if translation_value:
                    return translation_value
            
            return default or key
            
        except Exception as e:
            print(f"Error getting plugin translation for {plugin_name}.{key}: {e}")
            return default or key
    
    @classmethod
    def _get_from_config(cls, config: Dict, key: str, language: str) -> Optional[str]:
        """Plugin.json'dan çeviriyi al"""
        try:
            value = config.get(key, {})
            if isinstance(value, dict):
                # Çok dilli değer
                return value.get(language) or value.get('en') or value.get(list(value.keys())[0] if value else None)
            elif isinstance(value, str):
                # Tek dilli değer
                return value
        except:
            pass
        return None
    
    @classmethod
    def _get_from_locale(cls, plugin_name: str, key: str, language: str) -> Optional[str]:
        """Plugin locale dosyasından çeviriyi al (Django i18n .po formatı)"""
        try:
            from django.utils import translation
            from django.utils.translation import gettext as _
            
            plugin_path = Path(settings.BASE_DIR) / 'plugins' / plugin_name
            locale_path = plugin_path / 'locale'
            
            # Django locale path'ini ekle
            if locale_path.exists():
                # Geçici olarak locale path'i ekle
                original_locale_paths = list(settings.LOCALE_PATHS)
                if str(locale_path) not in [str(p) for p in settings.LOCALE_PATHS]:
                    settings.LOCALE_PATHS = list(settings.LOCALE_PATHS) + [str(locale_path)]
                
                try:
                    # Django translation sistemini kullan
                    with translation.override(language):
                        # gettext ile çeviriyi al
                        # Not: Django'nun gettext sistemi .po dosyalarını otomatik yükler
                        # Ancak plugin-specific domain kullanmak için özel bir yaklaşım gerekebilir
                        pass
                finally:
                    # Orijinal locale paths'i geri yükle
                    settings.LOCALE_PATHS = original_locale_paths
            
            # Alternatif: .po dosyasını doğrudan parse et
            po_file = locale_path / language / 'LC_MESSAGES' / 'django.po'
            if po_file.exists():
                return cls._parse_po_file(po_file, key)
                
        except Exception as e:
            print(f"Error loading locale file for {plugin_name}: {e}")
        return None
    
    @classmethod
    def _parse_po_file(cls, po_file: Path, key: str) -> Optional[str]:
        """PO dosyasından çeviriyi parse et"""
        try:
            import re
            with open(po_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # msgid ve msgstr çiftlerini bul
            # Basit regex ile parse (tam .po parser yerine)
            pattern = rf'msgid\s+"{re.escape(key)}"\s+msgstr\s+"([^"]+)"'
            match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
            if match:
                return match.group(1).replace('\\n', '\n').replace('\\"', '"')
            
            # Alternatif: çok satırlı msgid/msgstr desteği
            # msgid "key"
            # msgstr "value"
            lines = content.split('\n')
            in_msgid = False
            in_msgstr = False
            current_msgid = ""
            current_msgstr = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith('msgid '):
                    in_msgid = True
                    in_msgstr = False
                    current_msgid = line[6:].strip('"')
                elif line.startswith('msgstr '):
                    in_msgid = False
                    in_msgstr = True
                    current_msgstr = line[7:].strip('"')
                    if current_msgid == key and current_msgstr:
                        return current_msgstr.replace('\\n', '\n').replace('\\"', '"')
                elif in_msgid and line.startswith('"'):
                    current_msgid += line.strip('"')
                elif in_msgstr and line.startswith('"'):
                    current_msgstr += line.strip('"')
                    if current_msgid == key and current_msgstr:
                        return current_msgstr.replace('\\n', '\n').replace('\\"', '"')
                        
        except Exception as e:
            print(f"Error parsing PO file {po_file}: {e}")
        return None
    
    @classmethod
    def get_supported_languages(cls, plugin_name: str) -> list:
        """Plugin'in desteklediği dilleri al"""
        try:
            from .registry import PluginRegistry
            registry = PluginRegistry()
            plugin_info = registry.get_plugin(plugin_name)
            
            if not plugin_info:
                return ['en']  # Default
            
            config = plugin_info.get('config', {})
            
            # plugin.json'da supported_languages varsa onu kullan
            if 'supported_languages' in config:
                return config['supported_languages']
            
            # Yoksa, display_name veya description'dan desteklenen dilleri çıkar
            display_name = config.get('display_name', {})
            if isinstance(display_name, dict):
                languages = list(display_name.keys())
                # Sistem dilleriyle kesişim al
                system_languages = [lang[0] for lang in settings.LANGUAGES]
                return [lang for lang in languages if lang in system_languages]
            
            return ['en']  # Default
            
        except Exception as e:
            print(f"Error getting supported languages for {plugin_name}: {e}")
            return ['en']
    
    @classmethod
    def get_best_language(cls, plugin_name: str, user_language: Optional[str] = None) -> str:
        """
        Plugin için en uygun dili seç
        
        Args:
            plugin_name: Plugin adı
            user_language: Kullanıcının tercih ettiği dil
        
        Returns:
            Seçilen dil kodu
        """
        if user_language is None:
            user_language = translation.get_language() or settings.LANGUAGE_CODE
        
        # Dil kodunu normalize et
        user_language = user_language.split('-')[0].lower()
        
        # Plugin'in desteklediği dilleri al
        supported = cls.get_supported_languages(plugin_name)
        
        # Kullanıcı dili destekleniyorsa onu kullan
        if user_language in supported:
            return user_language
        
        # Desteklenmiyorsa, sistem dillerinden birini dene
        system_languages = [lang[0] for lang in settings.LANGUAGES]
        for lang in system_languages:
            if lang in supported:
                return lang
        
        # Hiçbiri yoksa default (genellikle 'en')
        return supported[0] if supported else 'en'
    
    @classmethod
    def clear_cache(cls, plugin_name: Optional[str] = None):
        """Cache'i temizle"""
        if plugin_name:
            # Belirli bir plugin'in cache'ini temizle
            keys_to_remove = [key for key in cls._cache.keys() if key.startswith(f"{plugin_name}_")]
            for key in keys_to_remove:
                del cls._cache[key]
        else:
            # Tüm cache'i temizle
            cls._cache.clear()


def get_plugin_translation(plugin_name: str, key: str, default: Optional[str] = None, 
                          language: Optional[str] = None) -> str:
    """
    Plugin çevirisini al (helper function)
    
    Usage in templates:
        {{ plugin_name|plugin_trans:"display_name" }}
    """
    return PluginI18n.get_plugin_translation(plugin_name, key, default, language)


def get_plugin_best_language(plugin_name: str, user_language: Optional[str] = None) -> str:
    """Plugin için en uygun dili seç (helper function)"""
    return PluginI18n.get_best_language(plugin_name, user_language)

