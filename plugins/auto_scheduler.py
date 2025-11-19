"""
Auto Scheduler - Plugin'lerin plugin.json'dan otomatik zamanlanmış görev oluşturma
"""

from typing import Dict, List, Optional
from .registry import PluginRegistry
from .scheduler import PluginScheduler
from .utils import get_plugin_setting


def initialize_plugin_tasks(plugin_name: str, plugin_config: Dict) -> List[str]:
    """
    Plugin'in plugin.json'dan zamanlanmış görevlerini oluştur
    
    Returns:
        Oluşturulan task_id'lerin listesi
    """
    scheduler = PluginScheduler()
    created_tasks = []
    
    # plugin.json'dan scheduled_tasks bölümünü al
    scheduled_tasks_config = plugin_config.get('scheduled_tasks', [])
    
    if not scheduled_tasks_config:
        return created_tasks
    
    for task_config in scheduled_tasks_config:
        try:
            # Task ID oluştur (plugin_name + endpoint'ten hash)
            endpoint = task_config.get('endpoint', '')
            task_id = f"{plugin_name}_{endpoint.replace('/', '_').replace(' ', '_')}"
            
            # Zaten var mı kontrol et
            existing_task = scheduler.get_task(task_id)
            if existing_task:
                # Mevcut görev varsa güncelleme yapma, sadece yeni görevler oluştur
                continue
            
            # Zamanlama bilgilerini al
            schedule_type = task_config.get('schedule_type', 'daily')
            schedule_time = task_config.get('schedule_time', '00:00')
            schedule_cron = task_config.get('schedule_cron')
            schedule_days = task_config.get('schedule_days')
            schedule_day = task_config.get('schedule_day')
            task_data = task_config.get('data', {})
            enabled = task_config.get('enabled', True)
            
            # API key'i al (eğer gerekliyse)
            api_key = None
            if task_config.get('requires_api_key', True):
                api_key = get_plugin_setting(plugin_name, 'api_key', user=None, default='')
            
            # Görevi oluştur
            success = scheduler.schedule_task(
                task_id=task_id,
                plugin_name=plugin_name,
                endpoint=endpoint,
                schedule_type=schedule_type,
                schedule_time=schedule_time,
                schedule_cron=schedule_cron,
                schedule_days=schedule_days,
                schedule_day=schedule_day,
                data=task_data,
                api_key=api_key
            )
            
            if success:
                # Eğer disabled ise devre dışı bırak
                if not enabled:
                    scheduler.disable_task(task_id)
                
                created_tasks.append(task_id)
                print(f"✓ Created scheduled task for plugin {plugin_name}: {task_id}")
            else:
                print(f"✗ Failed to create scheduled task for plugin {plugin_name}: {task_id}")
                
        except Exception as e:
            print(f"✗ Error creating scheduled task for plugin {plugin_name}: {e}")
            import traceback
            traceback.print_exc()
    
    return created_tasks


def initialize_all_plugin_tasks():
    """Tüm plugin'lerin zamanlanmış görevlerini oluştur"""
    registry = PluginRegistry()
    registry.load_all_plugins()
    
    all_created = []
    for plugin_info in registry.get_all_plugins():
        config = plugin_info.get('config', {})
        plugin_name = config.get('name')
        
        if plugin_name:
            created = initialize_plugin_tasks(plugin_name, config)
            all_created.extend(created)
    
    return all_created

