from django.urls import path
from . import views

app_name = 'firewall'

urlpatterns = [
    # Ana firewall seçim sayfası
    path('', views.firewall_selection, name='selection'),
    
    # UFW yönetimi
    path('ufw/', views.ufw_management, name='ufw'),
    path('ufw/api/status/', views.ufw_status_api, name='ufw_status_api'),
    path('ufw/api/rules/', views.ufw_rules_api, name='ufw_rules_api'),
    path('ufw/api/toggle/', views.ufw_toggle_api, name='ufw_toggle_api'),
    
    # iptables yönetimi
    path('iptables/', views.iptables_management, name='iptables'),
    path('iptables/api/status/', views.iptables_status_api, name='iptables_status_api'),
    path('iptables/api/rules/', views.iptables_rules_api, name='iptables_rules_api'),
    path('iptables/api/chains/', views.iptables_chain_api, name='iptables_chain_api'),
    path('iptables/api/delete-rule/', views.iptables_delete_rule_api, name='iptables_delete_rule_api'),
    path('iptables/api/delete-rule-by-spec/', views.iptables_delete_rule_by_spec_api, name='iptables_delete_rule_by_spec_api'),
    path('iptables/api/flush-chain/', views.iptables_flush_chain_api, name='iptables_flush_chain_api'),
    
    # firewalld yönetimi
    path('firewalld/', views.firewalld_management, name='firewalld'),
    path('firewalld/api/status/', views.firewalld_status_api, name='firewalld_status_api'),
    path('firewalld/api/rules/', views.firewalld_rules_api, name='firewalld_rules_api'),
    path('firewalld/api/toggle/', views.firewalld_toggle_api, name='firewalld_toggle_api'),
]
