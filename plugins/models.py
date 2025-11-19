"""
Plugin Models
Plugin ayarlarını veritabanında saklamak için
"""

from django.db import models
from django.contrib.auth.models import User


class PluginSetting(models.Model):
    """Plugin ayarları"""
    plugin_name = models.CharField(max_length=100, db_index=True)
    setting_key = models.CharField(max_length=100)
    setting_value = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plugins_settings'
        unique_together = ['plugin_name', 'setting_key', 'user']
        indexes = [
            models.Index(fields=['plugin_name', 'setting_key']),
        ]
    
    @classmethod
    def get_setting(cls, plugin_name, setting_key, user=None, default=None):
        """Plugin ayarını al"""
        try:
            if user:
                setting = cls.objects.get(plugin_name=plugin_name, setting_key=setting_key, user=user)
            else:
                setting = cls.objects.get(plugin_name=plugin_name, setting_key=setting_key, user__isnull=True)
            return setting.setting_value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_setting(cls, plugin_name, setting_key, value, user=None):
        """Plugin ayarını kaydet"""
        setting, created = cls.objects.update_or_create(
            plugin_name=plugin_name,
            setting_key=setting_key,
            user=user if user else None,
            defaults={'setting_value': value}
        )
        return setting

