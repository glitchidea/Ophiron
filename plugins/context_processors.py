"""
Plugin Context Processors
Template'lere plugin bilgilerini sağlar
"""

from django.utils import translation
from .registry import PluginRegistry
from .i18n import PluginI18n


def plugins_menu(request):
    """Menü için plugin listesini kategorilere göre gruplar"""
    registry = PluginRegistry()
    enabled_plugins = registry.get_enabled_plugins()
    
    # Kategori tanımları
    CATEGORY_INFO = {
        'security': {
            'name': 'Security',
            'icon': 'fas fa-shield-alt',
            'display_name': {
                'en': 'Security',
                'tr': 'Güvenlik',
                'de': 'Sicherheit'
            }
        },
        'system': {
            'name': 'System',
            'icon': 'fas fa-server',
            'display_name': {
                'en': 'System',
                'tr': 'Sistem',
                'de': 'System'
            }
        },
        'network': {
            'name': 'Network',
            'icon': 'fas fa-network-wired',
            'display_name': {
                'en': 'Network',
                'tr': 'Ağ',
                'de': 'Netzwerk'
            }
        },
        'monitoring': {
            'name': 'Monitoring',
            'icon': 'fas fa-chart-line',
            'display_name': {
                'en': 'Monitoring',
                'tr': 'İzleme',
                'de': 'Überwachung'
            }
        },
        'automation': {
            'name': 'Automation',
            'icon': 'fas fa-robot',
            'display_name': {
                'en': 'Automation',
                'tr': 'Otomasyon',
                'de': 'Automatisierung'
            }
        },
        'development': {
            'name': 'Development',
            'icon': 'fas fa-code',
            'display_name': {
                'en': 'Development',
                'tr': 'Geliştirme',
                'de': 'Entwicklung'
            }
        },
        'storage': {
            'name': 'Storage',
            'icon': 'fas fa-database',
            'display_name': {
                'en': 'Storage',
                'tr': 'Depolama',
                'de': 'Speicher'
            }
        },
        'reporting': {
            'name': 'Reporting',
            'icon': 'fas fa-chart-bar',
            'display_name': {
                'en': 'Reporting',
                'tr': 'Raporlama',
                'de': 'Berichterstattung'
            }
        },
        'other': {
            'name': 'Other',
            'icon': 'fas fa-cube',
            'display_name': {
                'en': 'Other',
                'tr': 'Diğer',
                'de': 'Andere'
            }
        }
    }
    
    # Plugin'leri kategorilere göre grupla
    plugins_by_category = {}
    all_plugins = []
    
    for plugin_info in enabled_plugins:
        config = plugin_info['config']
        plugin_name = config.get('name')
        route = config.get('route')
        icon = config.get('icon', 'fas fa-cube')
        category = config.get('category', 'other')
        
        # Plugin i18n sistemi ile çeviriyi al
        display_name = PluginI18n.get_plugin_translation(
            plugin_name, 
            'display_name', 
            default=plugin_name
        )
        
        plugin_data = {
            'name': plugin_name,
            'display_name': display_name,
            'route': route,
            'icon': icon,
            'category': category,
        }
        
        all_plugins.append(plugin_data)
        
        # Kategoriye göre grupla
        if category not in plugins_by_category:
            plugins_by_category[category] = []
        plugins_by_category[category].append(plugin_data)
    
    # Kategorileri hazırla
    categories = []
    current_lang = translation.get_language() or 'en'
    
    for category_key, category_info in CATEGORY_INFO.items():
        if category_key in plugins_by_category:
            # Kategori çevirisini al
            category_display = category_info['display_name'].get(
                current_lang, 
                category_info['display_name'].get('en', category_info['name'])
            )
            
            categories.append({
                'key': category_key,
                'name': category_display,
                'icon': category_info['icon'],
                'plugins': plugins_by_category[category_key],
                'count': len(plugins_by_category[category_key])
            })
    
    # Kategorileri sırala (other en sonda)
    categories.sort(key=lambda x: (x['key'] == 'other', x['name']))
    
    return {
        'plugins_menu': all_plugins,  # Tüm pluginler (geriye dönük uyumluluk)
        'plugins_by_category': categories,  # Kategorilere göre gruplanmış
        'plugins_count': len(all_plugins),
    }

