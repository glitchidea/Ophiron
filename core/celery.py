"""
Celery Configuration for Ophiron
Background tasks için Celery yapılandırması
"""

import os
from celery import Celery
from celery.schedules import crontab

# Django settings modülünü ayarla
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Celery app oluştur
app = Celery('ophiron')

# Django settings'ten yapılandırma yükle
app.config_from_object('django.conf:settings', namespace='CELERY')

# Celery yapılandırması
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Istanbul',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 dakika
    task_soft_time_limit=25 * 60,  # 25 dakika
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periyodik tasklar (isteğe bağlı)
from celery.schedules import schedule

app.conf.beat_schedule = {
    # Process Monitor - Cache güncelleme (DİNAMİK INTERVAL)
    # Interval settings'ten okunur, varsayılan 1 saniye
    'update-process-monitor-cache': {
        'task': 'process_monitor.update_cache',
        'schedule': 1.0,  # Varsayılan 1 saniye (settings'ten override edilir)
    },
    # System Information - Cache güncelleme (DİNAMİK INTERVAL)
    # Interval settings'ten okunur, varsayılan 5 saniye
    'update-system-info-cache': {
        'task': 'system_information.update_system_metrics',
        'schedule': 5.0,  # Varsayılan 5 saniye (settings'ten override edilir)
    },
    # Service Monitoring - Cache güncelleme (DİNAMİK INTERVAL)
    # Interval settings'ten okunur, varsayılan 2 saniye
    'update-service-monitoring-cache': {
        'task': 'service_monitoring.update_cache',
        'schedule': 2.0,  # Varsayılan 2 saniye (settings'ten override edilir)
    },
    # Cache temizleme (her 30 dakika)
    'cleanup-expired-cache': {
        'task': 'process_monitor.cleanup_expired_cache',
        'schedule': crontab(minute='*/30'),
    },
    # SMTP automations (check every minute)
    'enqueue-email-automations': {
        'task': 'smtp.enqueue_due_automations',
        'schedule': 60.0,
    },
}

# Dinamik schedule için custom scheduler kullan
app.conf.beat_schedule_filename = 'celerybeat-schedule'

# Django uygulamalarından task'ları otomatik keşfet
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Debug için test task"""
    print(f'Request: {self.request!r}')

