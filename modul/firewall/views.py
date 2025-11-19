from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import subprocess
import json
import shutil
from . import iptables

# ===== FIREWALL SELECTION =====

def firewall_selection(request):
    """Firewall seçim sayfası"""
    return render(request, 'modules/firewall/selection.html')

# ===== UFW MANAGEMENT VIEWS =====

def ufw_management(request):
    """UFW yönetim sayfası"""
    return render(request, 'modules/firewall/ufw.html')

@csrf_exempt
def ufw_status_api(request):
    """UFW durum API'si"""
    try:
        # UFW durumunu kontrol et - sudo ile
        result = subprocess.run(['sudo', 'ufw', 'status'], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            # UFW aktif - output'ta "Status: active" kontrolü yap
            if 'Status: active' in result.stdout:
                return JsonResponse({
                    'success': True,
                    'available': True,
                    'status': 'active',
                    'message': 'UFW is active'
                })
            else:
                return JsonResponse({
                    'success': True,
                    'available': True,
                    'status': 'inactive',
                    'message': 'UFW is inactive'
                })
        else:
            # UFW kapalı veya hata
            return JsonResponse({
                'success': True,
                'available': False,
                'status': 'inactive',
                'message': 'UFW is inactive'
            })
    except subprocess.TimeoutExpired:
        return JsonResponse({
            'success': False,
            'available': False,
            'error': 'Timeout while checking UFW status',
            'message': 'Failed to check UFW status'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'available': False,
            'error': str(e),
            'message': 'Error checking UFW status'
        })

@csrf_exempt
def ufw_rules_api(request):
    """UFW kuralları API'si"""
    try:
        # UFW kurallarını listele - sudo ile
        result = subprocess.run(['sudo', 'ufw', 'status', 'numbered'], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            return JsonResponse({
                'success': True,
                'rules': result.stdout,
                'message': 'UFW rules retrieved successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.stderr,
                'message': 'Failed to retrieve UFW rules'
            })
    except subprocess.TimeoutExpired:
        return JsonResponse({
            'success': False,
            'error': 'Timeout while retrieving UFW rules',
            'message': 'Failed to retrieve UFW rules'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error retrieving UFW rules'
        })

@csrf_exempt
def ufw_toggle_api(request):
    """UFW açma/kapama API'si"""
    try:
        data = json.loads(request.body)
        action = data.get('action', 'enable')
        
        if action == 'enable':
            result = subprocess.run(['sudo', 'ufw', 'enable'], capture_output=True, text=True, timeout=10)
        else:
            result = subprocess.run(['sudo', 'ufw', 'disable'], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return JsonResponse({
                'success': True,
                'message': f'UFW {action}d successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.stderr,
                'message': f'Failed to {action} UFW'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error toggling UFW'
        })

# ===== IPTABLES MANAGEMENT VIEWS =====

def iptables_management(request):
    """iptables yönetim sayfası"""
    return render(request, 'modules/firewall/iptables.html')

@csrf_exempt
def iptables_status_api(request):
    """iptables durum API'si"""
    try:
        result = iptables.api_iptables_status()
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'available': False,
            'error': str(e),
            'message': 'Error checking iptables status'
        })

@csrf_exempt
def iptables_rules_api(request):
    """iptables kuralları API'si - Tüm tabloları içerir"""
    try:
        result = iptables.api_iptables_rules()
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error retrieving iptables rules'
        })

@csrf_exempt
def iptables_chain_api(request):
    """iptables chain bilgileri API'si"""
    try:
        # Tüm chain'leri listele
        result = subprocess.run(['iptables', '-L', '-n', '-v'], 
                              capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            return JsonResponse({
                'success': True,
                'chains': result.stdout,
                'message': 'iptables chains retrieved successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.stderr,
                'message': 'Failed to retrieve iptables chains'
            })
    except subprocess.TimeoutExpired:
        return JsonResponse({
            'success': False,
            'error': 'Timeout while retrieving iptables chains',
            'message': 'Failed to retrieve iptables chains'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error retrieving iptables chains'
        })

@csrf_exempt
def iptables_delete_rule_api(request):
    """iptables kural silme API'si"""
    try:
        data = json.loads(request.body)
        table = data.get('table', 'filter')
        chain = data.get('chain', 'INPUT')
        rule_number = data.get('rule_number')
        
        if rule_number is None:
            return JsonResponse({
                'success': False,
                'error': 'Rule number is required',
                'message': 'Rule number must be provided'
            })
        
        result = iptables.api_iptables_delete_rule(table, chain, rule_number)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data',
            'message': 'Invalid JSON data provided'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error deleting iptables rule'
        })

@csrf_exempt
def iptables_delete_rule_by_spec_api(request):
    """iptables kural spesifikasyonuna göre silme API'si"""
    try:
        data = json.loads(request.body)
        table = data.get('table', 'filter')
        chain = data.get('chain', 'INPUT')
        rule_spec = data.get('rule_spec', '')
        
        if not rule_spec:
            return JsonResponse({
                'success': False,
                'error': 'Rule specification is required',
                'message': 'Rule specification must be provided'
            })
        
        result = iptables.api_iptables_delete_rule_by_spec(table, chain, rule_spec)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data',
            'message': 'Invalid JSON data provided'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error deleting iptables rule'
        })

@csrf_exempt
def iptables_flush_chain_api(request):
    """iptables chain temizleme API'si"""
    try:
        data = json.loads(request.body)
        table = data.get('table', 'filter')
        chain = data.get('chain', 'INPUT')
        
        result = iptables.api_iptables_flush_chain(table, chain)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data',
            'message': 'Invalid JSON data provided'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error flushing iptables chain'
        })

# ===== FIREWALLD MANAGEMENT VIEWS =====

def firewalld_management(request):
    """firewalld yönetim sayfası"""
    return render(request, 'modules/firewall/firewalld.html')

@csrf_exempt
def firewalld_status_api(request):
    """firewalld durum API'si - UFW ve iptables ile aynı yaklaşım"""
    try:
        # Önce firewall-cmd komutunun var olup olmadığını kontrol et (sudo olmadan)
        if not shutil.which('firewall-cmd'):
            return JsonResponse({
                'success': True,
                'available': False,
                'status': 'not_installed',
                'message': 'firewalld is not installed on this system'
            })
        
        # firewalld durumunu kontrol et - sudo ile (UFW ve iptables gibi)
        # Not: firewall-cmd --state komutu firewalld çalışmıyorsa exit code 252 döndürür
        # ama komut çalıştırılabiliyorsa firewalld yüklü demektir
        result = subprocess.run(['sudo', 'firewall-cmd', '--state'], capture_output=True, text=True, timeout=10)
        
        # Komut çalıştırılabildi (FileNotFoundError yok) - firewalld yüklü demektir
        output = result.stdout.strip().lower() if result.stdout else ''
        stderr_output = result.stderr.strip().lower() if result.stderr else ''
        
        # Sudo hatası kontrolü - "Authorization failed" veya "password" hatası varsa
        if 'authorization failed' in stderr_output or 'password' in stderr_output.lower():
            # Sudo yetkisi yok, ama firewalld yüklü
            return JsonResponse({
                'success': True,
                'available': True,
                'status': 'unknown',
                'message': 'firewalld is installed but cannot check status (permission denied)'
            })
        
        # firewalld çalışıyor mu kontrol et
        if result.returncode == 0 and output == 'running':
            # firewalld aktif ve çalışıyor
            return JsonResponse({
                'success': True,
                'available': True,
                'status': 'active',
                'message': 'firewalld is active'
            })
        else:
            # firewalld yüklü ama çalışmıyor
            # exit code 252 veya "not running" mesajı = yüklü ama çalışmıyor
            # Komut çalıştırılabildiği için (FileNotFoundError yok) firewalld yüklü demektir
            return JsonResponse({
                'success': True,
                'available': True,
                'status': 'inactive',
                'message': 'firewalld is installed but not running'
            })
    except subprocess.TimeoutExpired:
        return JsonResponse({
            'success': False,
            'available': False,
            'error': 'Timeout while checking firewalld status',
            'message': 'Failed to check firewalld status'
        })
    except FileNotFoundError:
        # firewall-cmd komutu bulunamadı - firewalld yüklü değil
        return JsonResponse({
            'success': True,
            'available': False,
            'status': 'not_installed',
            'message': 'firewalld is not installed on this system'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'available': False,
            'error': str(e),
            'message': 'Error checking firewalld status'
        })

@csrf_exempt
def firewalld_rules_api(request):
    """firewalld kuralları API'si - Geçici ve kalıcı kuralları ayırt eder"""
    try:
        # Önce firewall-cmd komutunun var olup olmadığını kontrol et (sudo olmadan)
        if not shutil.which('firewall-cmd'):
            return JsonResponse({
                'success': False,
                'error': 'firewalld is not installed on this system',
                'message': 'firewalld is not installed on this system'
            })
        
        # Runtime kuralları (geçici + kalıcı) - sudo ile
        result_runtime = subprocess.run(['sudo', 'firewall-cmd', '--list-all'], capture_output=True, text=True, timeout=15)
        
        # Kalıcı kuralları - sudo ile
        result_permanent = subprocess.run(['sudo', 'firewall-cmd', '--permanent', '--list-all'], capture_output=True, text=True, timeout=15)
        
        # Sudo hatası kontrolü
        stderr_runtime = result_runtime.stderr.strip().lower() if result_runtime.stderr else ''
        stderr_permanent = result_permanent.stderr.strip().lower() if result_permanent.stderr else ''
        
        if 'authorization failed' in stderr_runtime or 'password' in stderr_runtime.lower():
            return JsonResponse({
                'success': False,
                'error': 'Permission denied: sudo access required',
                'message': 'Permission denied: sudo access required to retrieve firewalld rules'
            })
        
        # Runtime kuralları başarılıysa
        if result_runtime.returncode == 0:
            runtime_rules = result_runtime.stdout
            permanent_rules = result_permanent.stdout if result_permanent.returncode == 0 else ''
            
            # Her iki çıktıyı da döndür (geçici/kalıcı ayırımı için)
            return JsonResponse({
                'success': True,
                'rules': runtime_rules,
                'permanent_rules': permanent_rules,
                'message': 'firewalld rules retrieved successfully'
            })
        elif 'not running' in stderr_runtime or 'not running' in result_runtime.stdout.lower():
            # firewalld çalışmıyor ama yüklü - boş kurallar döndür
            return JsonResponse({
                'success': True,
                'rules': '',
                'permanent_rules': '',
                'message': 'firewalld is installed but not running'
            })
        else:
            # Diğer hatalar
            return JsonResponse({
                'success': False,
                'error': result_runtime.stderr if result_runtime.stderr else 'Unknown error',
                'message': 'Failed to retrieve firewalld rules'
            })
    except subprocess.TimeoutExpired:
        return JsonResponse({
            'success': False,
            'error': 'Timeout while retrieving firewalld rules',
            'message': 'Failed to retrieve firewalld rules'
        })
    except FileNotFoundError:
        # firewall-cmd komutu bulunamadı - firewalld yüklü değil
        return JsonResponse({
            'success': False,
            'error': 'firewalld is not installed on this system',
            'message': 'firewalld is not installed on this system'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error retrieving firewalld rules'
        })

@csrf_exempt
def firewalld_toggle_api(request):
    """firewalld açma/kapama API'si - UFW ile aynı yaklaşım"""
    try:
        data = json.loads(request.body)
        action = data.get('action', 'enable')
        
        # systemctl ile firewalld servisini yönet (tüm modern Linux dağıtımlarında çalışır)
        if action == 'enable':
            result = subprocess.run(['sudo', 'systemctl', 'start', 'firewalld'], capture_output=True, text=True, timeout=10)
        else:
            result = subprocess.run(['sudo', 'systemctl', 'stop', 'firewalld'], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return JsonResponse({
                'success': True,
                'message': f'firewalld {action}d successfully'
            })
        else:
            error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
            return JsonResponse({
                'success': False,
                'error': error_msg if error_msg else 'Unknown error',
                'message': f'Failed to {action} firewalld'
            })
    except FileNotFoundError:
        # systemctl komutu bulunamadı (çok eski sistemler)
        return JsonResponse({
            'success': False,
            'error': 'systemctl command not found',
            'message': 'systemctl is not available on this system'
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data',
            'message': 'Invalid request data'
        })
    except subprocess.TimeoutExpired:
        return JsonResponse({
            'success': False,
            'error': 'Timeout while toggling firewalld',
            'message': 'Timeout: firewalld toggle operation took too long'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error toggling firewalld'
        })