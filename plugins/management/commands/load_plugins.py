"""
Management command to load and register plugins
"""

from django.core.management.base import BaseCommand
from plugins.registry import PluginRegistry


class Command(BaseCommand):
    help = 'Load and register all plugins'

    def handle(self, *args, **options):
        registry = PluginRegistry()
        plugins = registry.load_all_plugins()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully loaded {len(plugins)} plugin(s)')
        )
        
        for plugin_name, plugin_info in plugins.items():
            self.stdout.write(f'  - {plugin_name}')

