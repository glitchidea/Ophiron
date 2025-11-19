from django.db import models
from django.utils import timezone
import json


class ProcessTopology(models.Model):
    """
    Süreç topolojisi ana modeli - sistem süreçlerinin genel durumunu tutar
    """
    name = models.CharField(max_length=100, verbose_name="Topoloji Adı")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    
    class Meta:
        verbose_name = "Süreç Topolojisi"
        verbose_name_plural = "Süreç Topolojileri"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class ProcessNode(models.Model):
    """
    Süreç düğümü modeli - her bir süreci temsil eder
    """
    PROCESS_STATUS_CHOICES = [
        ('R', 'Running'),
        ('S', 'Sleeping'),
        ('D', 'Disk Sleep'),
        ('Z', 'Zombie'),
        ('T', 'Stopped'),
        ('t', 'Tracing Stop'),
        ('X', 'Dead'),
        ('x', 'Dead'),
        ('K', 'Wakekill'),
        ('W', 'Waking'),
        ('P', 'Parked'),
    ]
    
    topology = models.ForeignKey(ProcessTopology, on_delete=models.CASCADE, related_name='nodes', verbose_name="Topoloji")
    pid = models.PositiveIntegerField(verbose_name="Process ID")
    name = models.CharField(max_length=255, verbose_name="Süreç Adı")
    status = models.CharField(max_length=1, choices=PROCESS_STATUS_CHOICES, verbose_name="Durum")
    user = models.CharField(max_length=100, verbose_name="Kullanıcı")
    cpu_percent = models.FloatField(default=0.0, verbose_name="CPU Kullanımı (%)")
    memory_percent = models.FloatField(default=0.0, verbose_name="Bellek Kullanımı (%)")
    memory_rss = models.BigIntegerField(default=0, verbose_name="RSS Bellek (KB)")
    memory_vms = models.BigIntegerField(default=0, verbose_name="VMS Bellek (KB)")
    num_threads = models.PositiveIntegerField(default=1, verbose_name="Thread Sayısı")
    create_time = models.DateTimeField(verbose_name="Oluşturulma Zamanı")
    start_time = models.DateTimeField(null=True, blank=True, verbose_name="Başlangıç Zamanı")
    parent_pid = models.PositiveIntegerField(null=True, blank=True, verbose_name="Ebeveyn PID")
    command_line = models.TextField(blank=True, verbose_name="Komut Satırı")
    working_directory = models.CharField(max_length=500, blank=True, verbose_name="Çalışma Dizini")
    environment = models.JSONField(default=dict, blank=True, verbose_name="Ortam Değişkenleri")
    
    # Graph pozisyon bilgileri
    x_position = models.FloatField(default=0.0, verbose_name="X Pozisyonu")
    y_position = models.FloatField(default=0.0, verbose_name="Y Pozisyonu")
    node_size = models.FloatField(default=1.0, verbose_name="Düğüm Boyutu")
    node_color = models.CharField(max_length=7, default="#007bff", verbose_name="Düğüm Rengi")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Kayıt Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    class Meta:
        verbose_name = "Süreç Düğümü"
        verbose_name_plural = "Süreç Düğümleri"
        unique_together = ['topology', 'pid']
        ordering = ['pid']
        indexes = [
            models.Index(fields=['topology', 'pid']),
            models.Index(fields=['status']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.name} (PID: {self.pid})"
    
    def get_status_display_color(self):
        """Durum rengini döndürür"""
        status_colors = {
            'R': '#28a745',  # Green - Running
            'S': '#17a2b8',  # Cyan - Sleeping
            'D': '#ffc107',  # Yellow - Disk Sleep
            'Z': '#dc3545',  # Red - Zombie
            'T': '#6c757d',  # Gray - Stopped
            't': '#6c757d',  # Gray - Tracing Stop
            'X': '#343a40',  # Dark - Dead
            'x': '#343a40',  # Dark - Dead
            'K': '#fd7e14',  # Orange - Wakekill
            'W': '#20c997',  # Teal - Waking
            'P': '#6f42c1',  # Purple - Parked
        }
        return status_colors.get(self.status, '#6c757d')
    
    def get_cpu_color(self):
        """CPU kullanımına göre renk döndürür"""
        if self.cpu_percent > 50:
            return '#dc3545'  # Red
        elif self.cpu_percent > 20:
            return '#ffc107'  # Yellow
        elif self.cpu_percent > 5:
            return '#17a2b8'  # Cyan
        else:
            return '#28a745'  # Green
    
    def get_memory_color(self):
        """Bellek kullanımına göre renk döndürür"""
        if self.memory_percent > 50:
            return '#dc3545'  # Red
        elif self.memory_percent > 20:
            return '#ffc107'  # Yellow
        elif self.memory_percent > 5:
            return '#17a2b8'  # Cyan
        else:
            return '#28a745'  # Green


class ProcessConnection(models.Model):
    """
    Süreç bağlantıları modeli - süreçler arası ilişkileri temsil eder
    """
    CONNECTION_TYPES = [
        ('parent_child', 'Ebeveyn-Çocuk'),
        ('network', 'Ağ Bağlantısı'),
        ('file', 'Dosya Paylaşımı'),
        ('memory', 'Bellek Paylaşımı'),
        ('signal', 'Sinyal'),
        ('pipe', 'Pipe'),
        ('socket', 'Socket'),
        ('shared_memory', 'Paylaşımlı Bellek'),
    ]
    
    topology = models.ForeignKey(ProcessTopology, on_delete=models.CASCADE, related_name='connections', verbose_name="Topoloji")
    source_node = models.ForeignKey(ProcessNode, on_delete=models.CASCADE, related_name='outgoing_connections', verbose_name="Kaynak Düğüm")
    target_node = models.ForeignKey(ProcessNode, on_delete=models.CASCADE, related_name='incoming_connections', verbose_name="Hedef Düğüm")
    connection_type = models.CharField(max_length=20, choices=CONNECTION_TYPES, verbose_name="Bağlantı Tipi")
    weight = models.FloatField(default=1.0, verbose_name="Ağırlık")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadata")
    
    # Graph görselleştirme
    line_color = models.CharField(max_length=7, default="#6c757d", verbose_name="Çizgi Rengi")
    line_width = models.FloatField(default=1.0, verbose_name="Çizgi Kalınlığı")
    is_directed = models.BooleanField(default=True, verbose_name="Yönlü")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    class Meta:
        verbose_name = "Süreç Bağlantısı"
        verbose_name_plural = "Süreç Bağlantıları"
        unique_together = ['topology', 'source_node', 'target_node', 'connection_type']
        ordering = ['connection_type', 'weight']
        indexes = [
            models.Index(fields=['topology', 'connection_type']),
            models.Index(fields=['source_node']),
            models.Index(fields=['target_node']),
        ]
    
    def __str__(self):
        return f"{self.source_node.name} -> {self.target_node.name} ({self.get_connection_type_display()})"
    
    def get_connection_color(self):
        """Bağlantı tipine göre renk döndürür"""
        type_colors = {
            'parent_child': '#007bff',  # Blue
            'network': '#28a745',       # Green
            'file': '#ffc107',          # Yellow
            'memory': '#17a2b8',        # Cyan
            'signal': '#dc3545',        # Red
            'pipe': '#6f42c1',          # Purple
            'socket': '#fd7e14',        # Orange
            'shared_memory': '#20c997', # Teal
        }
        return type_colors.get(self.connection_type, '#6c757d')


class ProcessSnapshot(models.Model):
    """
    Süreç anlık görüntüsü - belirli bir zamandaki sistem durumunu kaydeder
    """
    topology = models.ForeignKey(ProcessTopology, on_delete=models.CASCADE, related_name='snapshots', verbose_name="Topoloji")
    snapshot_name = models.CharField(max_length=100, verbose_name="Anlık Görüntü Adı")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Zaman Damgası")
    
    # Sistem bilgileri
    total_processes = models.PositiveIntegerField(default=0, verbose_name="Toplam Süreç Sayısı")
    running_processes = models.PositiveIntegerField(default=0, verbose_name="Çalışan Süreç Sayısı")
    sleeping_processes = models.PositiveIntegerField(default=0, verbose_name="Bekleyen Süreç Sayısı")
    zombie_processes = models.PositiveIntegerField(default=0, verbose_name="Zombie Süreç Sayısı")
    
    # Performans metrikleri
    total_cpu_percent = models.FloatField(default=0.0, verbose_name="Toplam CPU Kullanımı")
    total_memory_percent = models.FloatField(default=0.0, verbose_name="Toplam Bellek Kullanımı")
    load_average_1min = models.FloatField(default=0.0, verbose_name="1 Dakika Yük Ortalaması")
    load_average_5min = models.FloatField(default=0.0, verbose_name="5 Dakika Yük Ortalaması")
    load_average_15min = models.FloatField(default=0.0, verbose_name="15 Dakika Yük Ortalaması")
    
    # Sistem bilgileri
    system_info = models.JSONField(default=dict, blank=True, verbose_name="Sistem Bilgileri")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    
    class Meta:
        verbose_name = "Süreç Anlık Görüntüsü"
        verbose_name_plural = "Süreç Anlık Görüntüleri"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['topology', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.snapshot_name} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class ProcessEvent(models.Model):
    """
    Süreç olayları - süreçlerin yaşam döngüsündeki değişiklikleri kaydeder
    """
    EVENT_TYPES = [
        ('start', 'Başlatıldı'),
        ('stop', 'Durduruldu'),
        ('kill', 'Sonlandırıldı'),
        ('restart', 'Yeniden Başlatıldı'),
        ('status_change', 'Durum Değişikliği'),
        ('resource_change', 'Kaynak Değişikliği'),
        ('error', 'Hata'),
    ]
    
    topology = models.ForeignKey(ProcessTopology, on_delete=models.CASCADE, related_name='events', verbose_name="Topoloji")
    node = models.ForeignKey(ProcessNode, on_delete=models.CASCADE, related_name='events', verbose_name="Süreç Düğümü")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, verbose_name="Olay Tipi")
    message = models.TextField(verbose_name="Mesaj")
    severity = models.CharField(max_length=10, choices=[
        ('info', 'Bilgi'),
        ('warning', 'Uyarı'),
        ('error', 'Hata'),
        ('critical', 'Kritik'),
    ], default='info', verbose_name="Önem Derecesi")
    
    # Olay detayları
    old_value = models.TextField(blank=True, verbose_name="Eski Değer")
    new_value = models.TextField(blank=True, verbose_name="Yeni Değer")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadata")
    
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Zaman Damgası")
    
    class Meta:
        verbose_name = "Süreç Olayı"
        verbose_name_plural = "Süreç Olayları"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['topology', 'event_type']),
            models.Index(fields=['node', 'timestamp']),
            models.Index(fields=['severity']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.node.name} ({self.timestamp.strftime('%H:%M:%S')})"
