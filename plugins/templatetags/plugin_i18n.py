"""
Plugin i18n Template Tags
Template'lerde plugin çevirilerini kullanmak için
"""

from django import template
from django.utils.safestring import mark_safe
from plugins.i18n import PluginI18n

register = template.Library()


@register.filter(name='plugin_trans')
def plugin_trans_filter(value, key):
    """
    Plugin çevirisini al
    
    Usage:
        {{ plugin_name|plugin_trans:"display_name" }}
        {{ plugin_name|plugin_trans:"description" }}
    """
    if not value:
        return ""
    
    plugin_name = str(value)
    translation = PluginI18n.get_plugin_translation(plugin_name, key)
    return mark_safe(translation)


@register.simple_tag(name='plugin_i18n')
def plugin_i18n_tag(plugin_name, key, default=None):
    """
    Plugin çevirisini al (tag olarak)
    
    Usage:
        {% plugin_i18n "virustotal_scanner" "display_name" %}
        {% plugin_i18n "virustotal_scanner" "description" "Default description" %}
    """
    translation = PluginI18n.get_plugin_translation(plugin_name, key, default)
    return mark_safe(translation)


@register.simple_tag(name='plugin_lang')
def plugin_lang_tag(plugin_name):
    """
    Plugin için en uygun dili döndür
    
    Usage:
        {% plugin_lang "virustotal_scanner" as plugin_language %}
    """
    return PluginI18n.get_best_language(plugin_name)


@register.inclusion_tag('plugins/plugin_translation.html', takes_context=True)
def plugin_translations(context, plugin_name, *keys):
    """
    Birden fazla çeviriyi bir seferde al
    
    Usage:
        {% plugin_translations "virustotal_scanner" "display_name" "description" %}
    """
    translations = {}
    for key in keys:
        translations[key] = PluginI18n.get_plugin_translation(plugin_name, key)
    
    return {
        'translations': translations,
        'plugin_name': plugin_name,
    }

