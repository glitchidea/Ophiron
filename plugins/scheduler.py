"""
Plugin Scheduler - Zamanlanmış işlemler için PID tabanlı scheduler
Cron expression desteği ile
"""

import json
import subprocess
import os
import signal
import threading
import time
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable
from django.conf import settings
from django.utils import timezone


class PluginScheduler:
    """Plugin'ler için zamanlanmış işlemler scheduler'ı"""
    
    _instance = None
    _scheduled_tasks: Dict[str, Dict] = {}
    _running = False
    _thread: Optional[threading.Thread] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._lock = threading.Lock()
            self._tasks_file = Path(settings.BASE_DIR) / 'tmp' / 'plugins' / 'scheduled_tasks.json'
            self._tasks_file.parent.mkdir(parents=True, exist_ok=True)
            self.load_tasks()
    
    def start(self):
        """Scheduler'ı başlat"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
        print("Plugin Scheduler started")
    
    def stop(self):
        """Scheduler'ı durdur"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("Plugin Scheduler stopped")
    
    def _run_scheduler(self):
        """Scheduler ana döngüsü"""
        while self._running:
            try:
                now = timezone.now()
                
                with self._lock:
                    tasks_to_run = []
                    for task_id, task in list(self._scheduled_tasks.items()):
                        if not task.get('enabled', False):
                            continue
                        
                        next_run = task.get('next_run')
                        if next_run and isinstance(next_run, str):
                            try:
                                next_run = datetime.fromisoformat(next_run.replace('Z', '+00:00'))
                            except:
                                continue
                        
                        if next_run and next_run <= now:
                            tasks_to_run.append(task_id)
                
                # Görevleri çalıştır
                for task_id in tasks_to_run:
                    self._execute_task(task_id)
                
                # Bir sonraki çalışma zamanını hesapla
                time.sleep(60)  # Her dakika kontrol et
                
            except Exception as e:
                print(f"Error in scheduler loop: {e}")
                time.sleep(60)
    
    def _execute_task(self, task_id: str):
        """Görevi çalıştır (ephemeral process)"""
        task = self._scheduled_tasks.get(task_id)
        if not task:
            return
        
        try:
            plugin_name = task.get('plugin_name')
            endpoint = task.get('endpoint')
            data = task.get('data', {})
            api_key = task.get('api_key')
            
            # Embedded bridge kullanarak ephemeral process başlat
            from .embedded_bridge import EmbeddedGoBridge
            from .registry import PluginRegistry
            
            registry = PluginRegistry()
            registry.load_all_plugins()
            plugin_info = registry.get_plugin(plugin_name)
            
            if not plugin_info:
                print(f"Plugin {plugin_name} not found for scheduled task {task_id}")
                return
            
            config = plugin_info.get('config', {})
            bridge = EmbeddedGoBridge(config)
            
            # Request gönder
            response = bridge.request(
                method='POST',
                endpoint=endpoint,
                data=data,
                api_key=api_key,
                timeout=300  # 5 dakika timeout
            )
            
            # Son çalışma zamanını güncelle
            task['last_run'] = timezone.now().isoformat()
            task['next_run'] = self._calculate_next_run(task).isoformat()
            
            # Başarı/hata kaydı
            if response.status_code == 200:
                task['last_status'] = 'success'
                task['last_result'] = response.json()
            else:
                task['last_status'] = 'error'
                task['last_result'] = {'error': f'HTTP {response.status_code}'}
            
            self.save_tasks()
            
            print(f"Scheduled task {task_id} executed successfully")
            
        except Exception as e:
            print(f"Error executing scheduled task {task_id}: {e}")
            task['last_status'] = 'error'
            task['last_result'] = {'error': str(e)}
            task['last_run'] = timezone.now().isoformat()
            self.save_tasks()
    
    def _parse_cron_field(self, field: str, min_val: int, max_val: int) -> List[int]:
        """Cron field'ını parse et (örn: "*/5", "1,3,5", "1-10", "*")"""
        if field == '*':
            return list(range(min_val, max_val + 1))
        
        values = []
        parts = field.split(',')
        
        for part in parts:
            part = part.strip()
            
            # Range: "1-10"
            if '-' in part:
                start, end = map(int, part.split('-'))
                values.extend(range(start, end + 1))
            
            # Step: "*/5" veya "1-10/2"
            elif '/' in part:
                if part.startswith('*/'):
                    step = int(part[2:])
                    values.extend(range(min_val, max_val + 1, step))
                else:
                    range_part, step = part.split('/')
                    step = int(step)
                    if '-' in range_part:
                        start, end = map(int, range_part.split('-'))
                        values.extend(range(start, end + 1, step))
                    else:
                        start = int(range_part)
                        values.extend(range(start, max_val + 1, step))
            
            # Single value
            else:
                values.append(int(part))
        
        # Remove duplicates and sort
        return sorted(list(set(values)))
    
    def _calculate_next_run_from_cron(self, cron_expr: str, now: datetime) -> datetime:
        """Cron expression'dan bir sonraki çalışma zamanını hesapla"""
        # Cron format: "minute hour day month weekday"
        # Örnek: "0 6 * * *" (her gün saat 6:00)
        # Örnek: "*/15 * * * *" (her 15 dakikada bir)
        # Örnek: "0 0 1 * *" (her ayın 1'i saat 00:00)
        
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            # Geçersiz cron, default günlük
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        minute_field, hour_field, day_field, month_field, weekday_field = parts
        
        # Parse fields
        minutes = self._parse_cron_field(minute_field, 0, 59)
        hours = self._parse_cron_field(hour_field, 0, 23)
        days = self._parse_cron_field(day_field, 1, 31)
        months = self._parse_cron_field(month_field, 1, 12)
        weekdays = self._parse_cron_field(weekday_field, 0, 6)  # 0=Sunday, 6=Saturday (cron standard)
        
        # Python weekday: 0=Monday, 6=Sunday
        # Cron weekday: 0=Sunday, 6=Saturday
        # Dönüşüm: cron_weekday = (python_weekday + 1) % 7
        
        # Şu andan itibaren bir sonraki uygun zamanı bul
        current = now.replace(second=0, microsecond=0)
        
        # Maksimum 1 yıl ileriye bak (sonsuz döngüyü önlemek için)
        max_iterations = 365 * 24 * 60
        iteration = 0
        
        while iteration < max_iterations:
            # Mevcut dakika, saat, gün, ay, hafta günü kontrol et
            current_minute = current.minute
            current_hour = current.hour
            current_day = current.day
            current_month = current.month
            current_weekday = (current.weekday() + 1) % 7  # Python weekday'den cron weekday'e çevir
            
            # Dakika kontrolü
            if current_minute not in minutes:
                # Bir sonraki uygun dakikaya atla
                next_minutes = [m for m in minutes if m > current_minute]
                if next_minutes:
                    current = current.replace(minute=min(next_minutes))
                    iteration += 1
                    continue
                else:
                    # Bu saatte uygun dakika yok, bir sonraki saate geç
                    current = current.replace(minute=0) + timedelta(hours=1)
                    iteration += 1
                    continue
            
            # Saat kontrolü
            if current_hour not in hours:
                # Bir sonraki uygun saate atla
                next_hours = [h for h in hours if h > current_hour]
                if next_hours:
                    current = current.replace(hour=min(next_hours), minute=min(minutes))
                    iteration += 1
                    continue
                else:
                    # Bugün uygun saat yok, yarın saat 00:00'a geç
                    current = (current + timedelta(days=1)).replace(hour=min(hours), minute=min(minutes))
                    iteration += 1
                    continue
            
            # Ay kontrolü
            if current_month not in months:
                # Bir sonraki uygun aya atla
                next_months = [m for m in months if m > current_month]
                if next_months:
                    next_month = min(next_months)
                    try:
                        current = current.replace(month=next_month, day=1, hour=min(hours), minute=min(minutes))
                    except ValueError:
                        # Geçersiz tarih, bir sonraki aya geç
                        if current_month == 12:
                            current = current.replace(year=current.year + 1, month=1, day=1, hour=min(hours), minute=min(minutes))
                        else:
                            current = current.replace(month=current_month + 1, day=1, hour=min(hours), minute=min(minutes))
                else:
                    # Gelecek yıl
                    current = current.replace(year=current.year + 1, month=min(months), day=1, hour=min(hours), minute=min(minutes))
                iteration += 1
                continue
            
            # Gün ve hafta günü kontrolü (cron'da OR mantığı: day VEYA weekday)
            # Eğer ikisi de * değilse, en yakın olanı kullan
            day_match = day_field == '*' or current_day in days
            weekday_match = weekday_field == '*' or current_weekday in weekdays
            
            if not day_match and not weekday_match:
                # Ne gün ne de hafta günü uygun
                # Önce gün kontrolü yap
                if day_field != '*':
                    next_days = [d for d in days if d > current_day]
                    if next_days:
                        try:
                            current = current.replace(day=min(next_days), hour=min(hours), minute=min(minutes))
                            iteration += 1
                            continue
                        except ValueError:
                            # Geçersiz gün, bir sonraki aya geç
                            if current_month == 12:
                                current = current.replace(year=current.year + 1, month=1, day=min(days), hour=min(hours), minute=min(minutes))
                            else:
                                current = current.replace(month=current_month + 1, day=min(days), hour=min(hours), minute=min(minutes))
                            iteration += 1
                            continue
                    else:
                        # Bu ay uygun gün yok, bir sonraki aya geç
                        if current_month == 12:
                            current = current.replace(year=current.year + 1, month=1, day=min(days), hour=min(hours), minute=min(minutes))
                        else:
                            current = current.replace(month=current_month + 1, day=min(days), hour=min(hours), minute=min(minutes))
                        iteration += 1
                        continue
                
                # Sonra hafta günü kontrolü
                if weekday_field != '*':
                    next_weekdays = [w for w in weekdays if w > current_weekday]
                    if next_weekdays:
                        days_ahead = min(next_weekdays) - current_weekday
                    else:
                        # Gelecek hafta
                        days_ahead = 7 - current_weekday + min(weekdays)
                    
                    current = (current + timedelta(days=days_ahead)).replace(hour=min(hours), minute=min(minutes))
                    iteration += 1
                    continue
            
            # Eğer day_field ve weekday_field ikisi de * değilse ve sadece biri uyuyorsa
            # Cron standardına göre: day VEYA weekday uyuyorsa geçerli
            # Ama ikisi de belirtilmişse ve hiçbiri uymuyorsa yukarıdaki kontrol zaten hallediyor
            
            # Tüm kontroller geçti, bu zaman uygun
            if current > now:
                return current
            
            # Şu anki zaman uygunsa, bir sonraki dakikaya geç
            current = current + timedelta(minutes=1)
            iteration += 1
        
        # Maksimum iterasyon aşıldı, default döndür
        return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    def _calculate_next_run(self, task: Dict) -> datetime:
        """Bir sonraki çalışma zamanını hesapla"""
        schedule_type = task.get('schedule_type', 'daily')
        schedule_time = task.get('schedule_time', '00:00')
        schedule_cron = task.get('schedule_cron')
        
        now = timezone.now()
        
        # Cron expression varsa öncelik ver
        if schedule_type == 'custom' and schedule_cron:
            try:
                return self._calculate_next_run_from_cron(schedule_cron, now)
            except Exception as e:
                print(f"Error parsing cron expression '{schedule_cron}': {e}")
                # Fallback to daily
                schedule_type = 'daily'
        
        if schedule_type == 'daily':
            # Günlük - belirtilen saatte
            hour, minute = map(int, schedule_time.split(':'))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        
        elif schedule_type == 'weekly':
            # Haftalık - belirtilen günlerde ve saatte
            schedule_days = task.get('schedule_days', '0')  # 0=Monday, 6=Sunday
            days = [int(d) for d in schedule_days.split(',') if d.strip()]
            hour, minute = map(int, schedule_time.split(':'))
            
            # Bu hafta içinde bir sonraki günü bul
            current_weekday = now.weekday()  # 0=Monday, 6=Sunday
            for day in sorted(days):
                if day > current_weekday:
                    days_ahead = day - current_weekday
                    next_run = now + timedelta(days=days_ahead)
                    return next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Gelecek hafta
            next_week_day = min(days)
            days_ahead = 7 - current_weekday + next_week_day
            next_run = now + timedelta(days=days_ahead)
            return next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        elif schedule_type == 'monthly':
            # Aylık - her ayın belirtilen gününde
            schedule_day = task.get('schedule_day', 1)
            hour, minute = map(int, schedule_time.split(':'))
            
            next_run = now.replace(day=schedule_day, hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                # Gelecek ay
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
            return next_run
        
        # Default: günlük saat 00:00
        next_run = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        return next_run
    
    def schedule_task(self, task_id: str, plugin_name: str, endpoint: str, 
                     schedule_type: str, schedule_time: str = '00:00',
                     schedule_cron: Optional[str] = None, schedule_days: Optional[str] = None,
                     schedule_day: Optional[int] = None, data: Optional[Dict] = None,
                     api_key: Optional[str] = None) -> bool:
        """Yeni görev zamanla"""
        try:
            next_run = self._calculate_next_run({
                'schedule_type': schedule_type,
                'schedule_time': schedule_time,
                'schedule_cron': schedule_cron,
                'schedule_days': schedule_days,
                'schedule_day': schedule_day,
            })
            
            task = {
                'task_id': task_id,
                'plugin_name': plugin_name,
                'endpoint': endpoint,
                'schedule_type': schedule_type,
                'schedule_time': schedule_time,
                'schedule_cron': schedule_cron,
                'schedule_days': schedule_days,
                'schedule_day': schedule_day,
                'data': data or {},
                'api_key': api_key,
                'enabled': True,
                'next_run': next_run.isoformat(),
                'last_run': None,
                'last_status': None,
                'last_result': None,
                'created_at': timezone.now().isoformat(),
            }
            
            with self._lock:
                self._scheduled_tasks[task_id] = task
            
            self.save_tasks()
            return True
            
        except Exception as e:
            print(f"Error scheduling task: {e}")
            return False
    
    def unschedule_task(self, task_id: str) -> bool:
        """Görevi iptal et"""
        with self._lock:
            if task_id in self._scheduled_tasks:
                del self._scheduled_tasks[task_id]
                self.save_tasks()
                return True
        return False
    
    def enable_task(self, task_id: str) -> bool:
        """Görevi etkinleştir"""
        with self._lock:
            if task_id in self._scheduled_tasks:
                self._scheduled_tasks[task_id]['enabled'] = True
                self.save_tasks()
                return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """Görevi devre dışı bırak"""
        with self._lock:
            if task_id in self._scheduled_tasks:
                self._scheduled_tasks[task_id]['enabled'] = False
                self.save_tasks()
                return True
        return False
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Görev bilgisini al"""
        return self._scheduled_tasks.get(task_id)
    
    def get_tasks_by_plugin(self, plugin_name: str) -> List[Dict]:
        """Plugin'e ait tüm görevleri al"""
        return [task for task in self._scheduled_tasks.values() 
                if task.get('plugin_name') == plugin_name]
    
    def save_tasks(self):
        """Görevleri dosyaya kaydet"""
        try:
            with open(self._tasks_file, 'w') as f:
                json.dump(self._scheduled_tasks, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving tasks: {e}")
    
    def load_tasks(self):
        """Görevleri dosyadan yükle"""
        try:
            if self._tasks_file.exists():
                with open(self._tasks_file, 'r') as f:
                    self._scheduled_tasks = json.load(f)
        except Exception as e:
            print(f"Error loading tasks: {e}")
            self._scheduled_tasks = {}


# Scheduler'ı başlat (Django startup'ında)
def start_scheduler():
    """Scheduler'ı başlat (Django apps.py'de çağrılır)"""
    scheduler = PluginScheduler()
    scheduler.start()
    return scheduler

