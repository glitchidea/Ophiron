"""
Plugin Management Views
"""

import os
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from pathlib import Path
from .registry import PluginRegistry
from .base import BasePlugin
from .importer import PluginImporter


@login_required
def plugin_list_view(request):
    """Plugin listesi sayfası - kategori filtreleme ile"""
    registry = PluginRegistry()
    registry.load_all_plugins()
    
    # Kategori filtresi
    selected_category = request.GET.get('category', 'all')
    
    # Kategori tanımları
    CATEGORY_INFO = {
        'security': {'name': 'Security', 'icon': 'fas fa-shield-alt'},
        'network': {'name': 'Network', 'icon': 'fas fa-network-wired'},
        'monitoring': {'name': 'Monitoring', 'icon': 'fas fa-chart-line'},
        'automation': {'name': 'Automation', 'icon': 'fas fa-robot'},
        'development': {'name': 'Development', 'icon': 'fas fa-code'},
        'storage': {'name': 'Storage', 'icon': 'fas fa-database'},
        'other': {'name': 'Other', 'icon': 'fas fa-cube'},
    }
    
    plugins = []
    plugins_by_category = {}
    
    for plugin_info in registry.get_all_plugins():
        config = plugin_info.get('config', {})
        plugin = BasePlugin(config.get('name'), use_embedded=True)
        
        from .i18n import PluginI18n
        
        plugin_name = config.get('name')
        category = config.get('category', 'other')
        
        # Plugin i18n sistemi ile çevirileri al
        display_name = PluginI18n.get_plugin_translation(
            plugin_name, 
            'display_name', 
            default=plugin_name
        )
        description = PluginI18n.get_plugin_translation(
            plugin_name, 
            'description', 
            default='No description available.'
        )
        
        # Sudo gereksinimini kontrol et
        from .utils import check_plugin_sudo_requirement
        sudo_info = check_plugin_sudo_requirement(config)
        
        plugin_data = {
            'name': plugin_name,
            'display_name': display_name,
            'description': description,
            'version': config.get('version'),
            'icon': config.get('icon', 'fas fa-puzzle-piece'),
            'route': config.get('route'),
            'category': category,
            'enabled': plugin_info.get('enabled', True),
            'has_settings': bool(config.get('settings', {})),
            'sudo_required': sudo_info.get('sudo_required', False),
            'sudo_reason': sudo_info.get('sudo_reason', ''),
        }
        
        plugins.append(plugin_data)
        
        # Kategoriye göre grupla
        if category not in plugins_by_category:
            plugins_by_category[category] = []
        plugins_by_category[category].append(plugin_data)
    
    # Kategori filtresi uygula
    if selected_category != 'all' and selected_category in plugins_by_category:
        filtered_plugins = plugins_by_category[selected_category]
    else:
        filtered_plugins = plugins
    
    # Kategorileri hazırla (istatistiklerle)
    categories = []
    selected_category_name = 'All'
    
    for cat_key, cat_info in CATEGORY_INFO.items():
        count = len(plugins_by_category.get(cat_key, []))
        is_active = selected_category == cat_key
        if is_active:
            selected_category_name = cat_info['name']
        categories.append({
            'key': cat_key,
            'name': cat_info['name'],
            'icon': cat_info['icon'],
            'count': count,
            'active': is_active
        })
    
    # "All" kategorisi ekle
    categories.insert(0, {
        'key': 'all',
        'name': 'All',
        'icon': 'fas fa-th',
        'count': len(plugins),
        'active': selected_category == 'all'
    })
    if selected_category == 'all':
        selected_category_name = 'All'
    
    return render(request, 'plugins/plugin_list.html', {
        'plugins': filtered_plugins,
        'categories': categories,
        'selected_category': selected_category,
        'selected_category_name': selected_category_name,
        'total_count': len(plugins),
    })


@login_required
def plugin_settings_view(request, plugin_name):
    """Plugin ayarları sayfası"""
    registry = PluginRegistry()
    registry.load_all_plugins()
    
    plugin_info = registry.get_plugin(plugin_name)
    if not plugin_info:
        return redirect('plugins:list')
    
    config = plugin_info.get('config', {})
    plugin = BasePlugin(plugin_name, use_embedded=True)
    
    # Plugin ayarlarını al
    settings_config = config.get('settings', {})
    
    # Plugin i18n sistemi ile çevirileri al
    from .i18n import PluginI18n
    display_name = PluginI18n.get_plugin_translation(
        plugin_name, 
        'display_name', 
        default=plugin_name
    )
    description = PluginI18n.get_plugin_translation(
        plugin_name, 
        'description', 
        default='Plugin settings'
    )
    
    return render(request, 'plugins/plugin_settings.html', {
        'plugin': {
            'name': plugin_name,
            'display_name': display_name,
            'description': description,
            'version': config.get('version'),
            'icon': config.get('icon', 'fas fa-puzzle-piece'),
            'route': config.get('route'),
            'settings': settings_config,
        },
    })


@require_http_methods(["GET"])
@login_required
def plugin_settings_api(request, plugin_name):
    """Plugin ayarlarını getir (API)"""
    try:
        from .utils import get_plugin_setting
        
        registry = PluginRegistry()
        registry.load_all_plugins()
        
        plugin_info = registry.get_plugin(plugin_name)
        if not plugin_info:
            return JsonResponse({
                'status': 'error',
                'message': 'Plugin not found'
            }, status=404)
        
        config = plugin_info.get('config', {})
        settings_config = config.get('settings', {})
        
        # Mevcut ayar değerlerini al
        settings_values = {}
        for key, value_config in settings_config.items():
            setting_value = get_plugin_setting(plugin_name, key, user=request.user, default='')
            settings_values[key] = {
                'value': setting_value,
                'type': value_config.get('type', 'string'),
                'description': value_config.get('description', {}),
                'required': value_config.get('required', False),
            }
        
        return JsonResponse({
            'status': 'ok',
            'data': {
                'plugin_name': plugin_name,
                'settings': settings_values,
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_http_methods(["POST"])
@login_required
def plugin_settings_save_api(request, plugin_name):
    """Plugin ayarlarını kaydet (API)"""
    try:
        import json
        from .utils import set_plugin_setting
        
        registry = PluginRegistry()
        registry.load_all_plugins()
        
        plugin_info = registry.get_plugin(plugin_name)
        if not plugin_info:
            return JsonResponse({
                'status': 'error',
                'message': 'Plugin not found'
            }, status=404)
        
        config = plugin_info.get('config', {})
        settings_config = config.get('settings', {})
        
        data = json.loads(request.body)
        settings_data = data.get('settings', {})
        
        # Ayarları kaydet
        saved_settings = {}
        for key, value in settings_data.items():
            if key in settings_config:
                value_config = settings_config[key]
                is_secret = value_config.get('type') == 'password' or 'key' in key.lower() or 'secret' in key.lower()
                
                success = set_plugin_setting(
                    plugin_name,
                    key,
                    value,
                    user=request.user,
                    is_secret=is_secret
                )
                
                if success:
                    saved_settings[key] = 'saved'
                else:
                    saved_settings[key] = 'error'
        
        return JsonResponse({
            'status': 'ok',
            'message': 'Settings saved successfully',
            'data': {
                'saved_settings': saved_settings,
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_http_methods(["POST"])
@login_required
def plugin_import_validate_api(request):
    """Plugin import öncesi doğrulama API"""
    try:
        import tempfile
        import shutil
        
        # Check if files are uploaded (folder selection)
        if request.FILES:
            # Create temporary directory
            temp_dir = Path(tempfile.mkdtemp(prefix='ophiron_plugin_import_'))
            
            try:
                # Save uploaded files maintaining directory structure
                file_count = int(request.POST.get('file_count', 0))
                files_map = {}
                
                for i in range(file_count):
                    file_key = f'file_{i}'
                    path_key = f'path_{i}'
                    
                    if file_key in request.FILES and path_key in request.POST:
                        uploaded_file = request.FILES[file_key]
                        relative_path = request.POST[path_key]
                        
                        # Create full path in temp directory
                        file_path = temp_dir / relative_path
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Save file
                        with open(file_path, 'wb') as f:
                            for chunk in uploaded_file.chunks():
                                f.write(chunk)
                
                # Find plugin.json in temp directory
                plugin_json = None
                for json_file in temp_dir.rglob('plugin.json'):
                    plugin_json = json_file
                    break
                
                if not plugin_json:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return JsonResponse({
                        'success': False,
                        'error': 'plugin.json not found in selected folder'
                    }, status=400)
                
                # Use parent directory of plugin.json as plugin path
                plugin_path = plugin_json.parent
                
            except Exception as e:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return JsonResponse({
                    'success': False,
                'error': f'Error processing uploaded files: {str(e)}'
                }, status=400)
        else:
            # Legacy: path-based import
            data = json.loads(request.body)
            plugin_path = data.get('path', '').strip()
            
            if not plugin_path:
                return JsonResponse({
                    'success': False,
                    'error': 'Plugin path is required'
                }, status=400)
            
            # Path'i normalize et
            plugin_path = Path(plugin_path)
            
            # Absolute path yap
            if not plugin_path.is_absolute():
                # Relative path ise BASE_DIR'den başlat
                plugin_path = Path(settings.BASE_DIR) / plugin_path
            
            # Path'in var olduğunu kontrol et
            if not plugin_path.exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Plugin path does not exist'
                }, status=400)
        
        # Plugin'i doğrula
        importer = PluginImporter()
        preview = importer.get_plugin_preview(plugin_path)
        
        if not preview:
            if request.FILES and 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)
            return JsonResponse({
                'success': False,
                'error': 'Could not read plugin information'
            }, status=400)
        
        if not preview.get('valid'):
            if request.FILES and 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)
            return JsonResponse({
                'success': False,
                'error': preview.get('error', 'Invalid plugin')
            }, status=400)
        
        # i18n çevirileri ekle
        from .i18n import PluginI18n
        display_name = PluginI18n.get_plugin_translation(
            preview['name'],
            'display_name',
            default=preview['name']
        )
        description = PluginI18n.get_plugin_translation(
            preview['name'],
            'description',
            default='No description available.'
        )
        
        # Store temp_dir in session for import step
        if request.FILES and 'temp_dir' in locals():
            request.session['plugin_import_temp_dir'] = str(temp_dir)
        
        return JsonResponse({
            'success': True,
            'preview': {
                **preview,
                'display_name': display_name,
                'description': description,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in plugin_import_validate_api: {error_trace}")
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir, ignore_errors=True)
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
@login_required
def plugin_import_api(request):
    """Plugin import API"""
    try:
        import tempfile
        import shutil
        
        # Check if files are uploaded (folder selection) or if we have session temp_dir
        if request.FILES or ('plugin_import_temp_dir' in request.session):
            # Get temp directory from session or create new one
            temp_dir = None
            if 'plugin_import_temp_dir' in request.session:
                temp_dir = Path(request.session['plugin_import_temp_dir'])
                if not temp_dir.exists():
                    temp_dir = None
            
            if not temp_dir and request.FILES:
                # Create temporary directory
                temp_dir = Path(tempfile.mkdtemp(prefix='ophiron_plugin_import_'))
                
                # Save uploaded files maintaining directory structure
                file_count = int(request.POST.get('file_count', 0))
                
                for i in range(file_count):
                    file_key = f'file_{i}'
                    path_key = f'path_{i}'
                    
                    if file_key in request.FILES and path_key in request.POST:
                        uploaded_file = request.FILES[file_key]
                        relative_path = request.POST[path_key]
                        
                        # Create full path in temp directory
                        file_path = temp_dir / relative_path
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Save file
                        with open(file_path, 'wb') as f:
                            for chunk in uploaded_file.chunks():
                                f.write(chunk)
            
            if not temp_dir:
                return JsonResponse({
                    'success': False,
                    'error': 'No files uploaded and no session data found'
                }, status=400)
            
            # Find plugin.json in temp directory
            plugin_json = None
            for json_file in temp_dir.rglob('plugin.json'):
                plugin_json = json_file
                break
            
            if not plugin_json:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
                if 'plugin_import_temp_dir' in request.session:
                    del request.session['plugin_import_temp_dir']
                return JsonResponse({
                    'success': False,
                    'error': 'plugin.json not found in selected folder'
                }, status=400)
            
            # Use parent directory of plugin.json as plugin path
            plugin_path = plugin_json.parent
            plugin_name = None
            
        else:
            # Legacy: path-based import
            data = json.loads(request.body)
            plugin_path = data.get('path', '').strip()
            plugin_name = data.get('name', '').strip() or None
            
            if not plugin_path:
                return JsonResponse({
                    'success': False,
                    'error': 'Plugin path is required'
                }, status=400)
            
            # Path'i normalize et
            plugin_path = Path(plugin_path)
            
            # Absolute path yap
            if not plugin_path.is_absolute():
                plugin_path = Path(settings.BASE_DIR) / plugin_path
            
            # Path'in var olduğunu kontrol et
            if not plugin_path.exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Plugin path does not exist'
                }, status=400)
        
        # Plugin'i import et
        importer = PluginImporter()
        success, imported_name, error = importer.import_plugin(plugin_path, plugin_name)
        
        # Clean up temp directory
        if request.FILES and 'temp_dir' in locals() and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
            if 'plugin_import_temp_dir' in request.session:
                del request.session['plugin_import_temp_dir']
        
        if not success:
            return JsonResponse({
                'success': False,
                'error': error
            }, status=400)
        
        # Registry'yi yeniden yükle
        registry = PluginRegistry()
        registry.load_all_plugins()
        
        return JsonResponse({
            'success': True,
            'message': f'Plugin "{imported_name}" imported successfully',
            'plugin_name': imported_name
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in plugin_import_api: {error_trace}")
        if 'temp_dir' in locals() and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        if 'plugin_import_temp_dir' in request.session:
            del request.session['plugin_import_temp_dir']
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
@login_required
def plugin_scheduler_tasks_api(request, plugin_name):
    """Plugin'e ait zamanlanmış görevleri getir"""
    try:
        from .scheduler import PluginScheduler
        
        scheduler = PluginScheduler()
        tasks = scheduler.get_tasks_by_plugin(plugin_name)
        
        return JsonResponse({
            'status': 'ok',
            'data': {
                'tasks': tasks,
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_http_methods(["POST"])
@login_required
def plugin_scheduler_schedule_api(request, plugin_name):
    """Yeni zamanlanmış görev oluştur"""
    try:
        import json
        import uuid
        from .scheduler import PluginScheduler
        from .utils import get_plugin_setting
        
        data = json.loads(request.body)
        
        task_id = data.get('task_id') or f"{plugin_name}_{uuid.uuid4().hex[:8]}"
        endpoint = data.get('endpoint')
        schedule_type = data.get('schedule_type', 'daily')
        schedule_time = data.get('schedule_time', '00:00')
        schedule_cron = data.get('schedule_cron')
        schedule_days = data.get('schedule_days')
        schedule_day = data.get('schedule_day')
        task_data = data.get('data', {})
        
        # API key'i al
        api_key = get_plugin_setting(plugin_name, 'api_key', user=request.user, default='')
        
        scheduler = PluginScheduler()
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
            return JsonResponse({
                'status': 'ok',
                'message': 'Task scheduled successfully',
                'data': {
                    'task_id': task_id,
                }
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to schedule task'
            }, status=500)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_http_methods(["POST"])
@login_required
def plugin_scheduler_unschedule_api(request, plugin_name, task_id):
    """Zamanlanmış görevi iptal et"""
    try:
        from .scheduler import PluginScheduler
        
        scheduler = PluginScheduler()
        success = scheduler.unschedule_task(task_id)
        
        if success:
            return JsonResponse({
                'status': 'ok',
                'message': 'Task unscheduled successfully'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Task not found'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_http_methods(["POST"])
@login_required
def plugin_scheduler_toggle_api(request, plugin_name, task_id):
    """Zamanlanmış görevi etkinleştir/devre dışı bırak"""
    try:
        import json
        from .scheduler import PluginScheduler
        
        data = json.loads(request.body)
        enabled = data.get('enabled', True)
        
        scheduler = PluginScheduler()
        if enabled:
            success = scheduler.enable_task(task_id)
        else:
            success = scheduler.disable_task(task_id)
        
        if success:
            return JsonResponse({
                'status': 'ok',
                'message': f'Task {"enabled" if enabled else "disabled"} successfully'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Task not found'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_http_methods(["POST"])
@login_required
def plugin_fix_permissions_api(request, plugin_name):
    """Plugin dosya izinlerini düzelt (sudo kullanmadan)"""
    try:
        from .utils import fix_plugin_file_permissions
        
        success, message = fix_plugin_file_permissions(plugin_name)
        
        if success:
            return JsonResponse({
                'status': 'ok',
                'message': message
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': message
            }, status=500)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_http_methods(["DELETE"])
@login_required
def plugin_delete_api(request, plugin_name):
    """Plugin'i sil (klasör, ayarlar ve scheduler görevleri dahil)"""
    try:
        import shutil
        from .registry import PluginRegistry
        from .models import PluginSetting
        from .scheduler import PluginScheduler
        
        registry = PluginRegistry()
        registry.load_all_plugins()
        
        # Plugin'in var olup olmadığını kontrol et
        plugin_info = registry.get_plugin(plugin_name)
        if not plugin_info:
            return JsonResponse({
                'status': 'error',
                'message': f'Plugin "{plugin_name}" not found'
            }, status=404)
        
        # Plugin klasörünü bul
        plugin_path = plugin_info.get('path')
        if not plugin_path or not plugin_path.exists():
            return JsonResponse({
                'status': 'error',
                'message': f'Plugin directory not found for "{plugin_name}"'
            }, status=404)
        
        # 1. Scheduler görevlerini temizle
        try:
            scheduler = PluginScheduler()
            # Plugin'e ait tüm görevleri bul ve sil
            tasks_to_remove = []
            for task_id, task in scheduler._scheduled_tasks.items():
                if task.get('plugin_name') == plugin_name:
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                scheduler.unschedule_task(task_id)
        except Exception as e:
            print(f"Warning: Could not clean scheduler tasks: {e}")
        
        # 2. Plugin ayarlarını veritabanından sil
        try:
            deleted_count = PluginSetting.objects.filter(plugin_name=plugin_name).delete()[0]
            print(f"Deleted {deleted_count} plugin settings for {plugin_name}")
        except Exception as e:
            print(f"Warning: Could not delete plugin settings: {e}")
        
        # 3. Plugin klasörünü sil
        try:
            shutil.rmtree(plugin_path)
            print(f"Deleted plugin directory: {plugin_path}")
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to delete plugin directory: {str(e)}'
            }, status=500)
        
        # 4. Registry'den kaldır
        registry.unregister_plugin(plugin_name)
        
        # 5. Static files'ı temizle (varsa)
        try:
            static_path = Path(settings.BASE_DIR) / 'staticfiles' / 'plugins' / plugin_name
            if static_path.exists():
                shutil.rmtree(static_path)
        except Exception as e:
            print(f"Warning: Could not delete static files: {e}")
        
        return JsonResponse({
            'status': 'ok',
            'message': f'Plugin "{plugin_name}" deleted successfully'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
