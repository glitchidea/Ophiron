from django.apps import AppConfig


class PluginsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins'
    verbose_name = 'Ophiron Plugins'

    def ready(self):
        """Plugin sistemini başlat"""
        from .registry import PluginRegistry
        from .scheduler import start_scheduler
        from .auto_scheduler import initialize_all_plugin_tasks
        from django.conf import settings
        from pathlib import Path
        
        registry = PluginRegistry()
        registry.load_all_plugins()
        
        # Plugin locale path'lerini ekle
        try:
            plugins_dir = Path(settings.BASE_DIR) / 'plugins'
            for plugin_dir in plugins_dir.iterdir():
                if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
                    locale_path = plugin_dir / 'locale'
                    if locale_path.exists():
                        locale_path_str = str(locale_path)
                        if locale_path_str not in [str(p) for p in settings.LOCALE_PATHS]:
                            settings.LOCALE_PATHS = list(settings.LOCALE_PATHS) + [locale_path_str]
                            print(f"✓ Added locale path for plugin: {plugin_dir.name}")
        except Exception as e:
            print(f"Warning: Could not add plugin locale paths: {e}")
        
        # Plugin'lerin otomatik zamanlanmış görevlerini oluştur
        try:
            initialize_all_plugin_tasks()
        except Exception as e:
            print(f"Warning: Could not initialize plugin scheduled tasks: {e}")
        
        # Scheduler'ı başlat
        try:
            start_scheduler()
        except Exception as e:
            print(f"Warning: Could not start plugin scheduler: {e}")

