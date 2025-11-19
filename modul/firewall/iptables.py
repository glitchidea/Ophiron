# ===== IPTABLES RULE MANAGEMENT MODULE =====
# Bu modül iptables kurallarını yönetmek için kullanılır
# Kural ekleme, silme, listeleme ve düzenleme işlemleri

import subprocess
import json
import re
from typing import Dict, List, Optional, Tuple

class IptablesManager:
    """iptables kurallarını yönetmek için ana sınıf"""
    
    def __init__(self):
        self.sudo_required = True
        self.timeout = 15
    
    def _run_command(self, command: List[str], timeout: int = None) -> Tuple[int, str, str]:
        """Komut çalıştır ve sonucu döndür"""
        if timeout is None:
            timeout = self.timeout
            
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timeout"
        except Exception as e:
            return -1, "", str(e)
    
    def get_status(self) -> Dict:
        """iptables durumunu kontrol et"""
        try:
            # iptables durumunu kontrol et
            returncode, stdout, stderr = self._run_command(['sudo', 'iptables', '-L', '-n'])
            
            if returncode == 0:
                return {
                    'success': True,
                    'available': True,
                    'status': 'active',
                    'message': 'iptables is active'
                }
            else:
                return {
                    'success': True,
                    'available': False,
                    'status': 'inactive',
                    'message': 'iptables is not available'
                }
        except Exception as e:
            return {
                'success': False,
                'available': False,
                'error': str(e),
                'message': 'Error checking iptables status'
            }
    
    def get_rules(self) -> Dict:
        """Tüm iptables kurallarını listele"""
        try:
            # Tüm tabloları listele
            tables = ['filter', 'nat', 'mangle', 'raw', 'security']
            all_rules = []
            
            for table in tables:
                # Her tablo için kuralları al
                returncode, stdout, stderr = self._run_command([
                    'sudo', 'iptables', '-t', table, '-L', '-n', '--line-numbers'
                ])
                
                if returncode == 0 and stdout.strip():
                    # Tablo başlığı ekle
                    all_rules.append(f"=== {table.upper()} TABLE ===")
                    all_rules.append(stdout)
                    all_rules.append("")  # Boş satır ekle
                elif returncode != 0:
                    # Sudo olmadan dene
                    returncode_no_sudo, stdout_no_sudo, stderr_no_sudo = self._run_command([
                        'iptables', '-t', table, '-L', '-n', '--line-numbers'
                    ])
                    if returncode_no_sudo == 0 and stdout_no_sudo.strip():
                        all_rules.append(f"=== {table.upper()} TABLE ===")
                        all_rules.append(stdout_no_sudo)
                        all_rules.append("")
            
            if all_rules:
                return {
                    'success': True,
                    'rules': '\n'.join(all_rules),
                    'message': 'iptables rules retrieved successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'No rules found or permission denied',
                    'message': 'No iptables rules found or insufficient permissions'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error retrieving iptables rules'
            }
    
    def delete_rule(self, table: str, chain: str, rule_number: int) -> Dict:
        """Belirtilen kuralı sil"""
        try:
            # Önce kuralın var olup olmadığını kontrol et
            check_returncode, check_stdout, check_stderr = self._run_command([
                'sudo', 'iptables', '-t', table, '-L', chain, '-n', '--line-numbers'
            ])
            
            if check_returncode != 0:
                return {
                    'success': False,
                    'error': f'Chain {chain} not found in table {table}',
                    'message': f'Chain {chain} not found in table {table}'
                }
            
            # Kural numarasının geçerli olup olmadığını kontrol et
            lines = check_stdout.strip().split('\n')
            valid_rule_numbers = []
            for line in lines:
                if line.strip() and not line.startswith('Chain') and not line.startswith('target'):
                    parts = line.split()
                    if parts and parts[0].isdigit():
                        valid_rule_numbers.append(int(parts[0]))
            
            if rule_number not in valid_rule_numbers:
                return {
                    'success': False,
                    'error': f'Rule number {rule_number} not found in chain {chain}',
                    'message': f'Rule number {rule_number} not found in chain {chain}. Available rules: {valid_rule_numbers}'
                }
            
            # Kuralı sil
            returncode, stdout, stderr = self._run_command([
                'sudo', 'iptables', '-t', table, '-D', chain, str(rule_number)
            ])
            
            if returncode == 0:
                return {
                    'success': True,
                    'message': f'Rule {rule_number} deleted successfully from {table}.{chain}'
                }
            else:
                # Hata mesajını daha anlaşılır hale getir
                error_msg = stderr.strip() if stderr.strip() else stdout.strip()
                if 'No chain/target/match by that name' in error_msg:
                    error_msg = f'Chain {chain} or rule {rule_number} not found in table {table}'
                elif 'Bad rule' in error_msg:
                    error_msg = f'Invalid rule number {rule_number} in chain {chain}'
                
                return {
                    'success': False,
                    'error': error_msg,
                    'message': f'Failed to delete rule {rule_number} from {table}.{chain}: {error_msg}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error deleting iptables rule'
            }
    
    def delete_rule_by_spec(self, table: str, chain: str, rule_spec: str) -> Dict:
        """Kural spesifikasyonuna göre kural sil"""
        try:
            # Kuralı sil
            returncode, stdout, stderr = self._run_command([
                'sudo', 'iptables', '-t', table, '-D', chain] + rule_spec.split()
            )
            
            if returncode == 0:
                return {
                    'success': True,
                    'message': f'Rule deleted successfully from {table}.{chain}'
                }
            else:
                return {
                    'success': False,
                    'error': stderr,
                    'message': f'Failed to delete rule from {table}.{chain}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error deleting iptables rule'
            }
    
    def flush_chain(self, table: str, chain: str) -> Dict:
        """Belirtilen chain'i temizle"""
        try:
            # Chain'i temizle
            returncode, stdout, stderr = self._run_command([
                'sudo', 'iptables', '-t', table, '-F', chain
            ])
            
            if returncode == 0:
                return {
                    'success': True,
                    'message': f'Chain {chain} flushed successfully in table {table}'
                }
            else:
                return {
                    'success': False,
                    'error': stderr,
                    'message': f'Failed to flush chain {chain} in table {table}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error flushing iptables chain'
            }
    
    def add_rule(self, table: str, chain: str, rule_spec: str) -> Dict:
        """Yeni kural ekle"""
        try:
            # Kural ekle
            returncode, stdout, stderr = self._run_command([
                'sudo', 'iptables', '-t', table, '-A', chain] + rule_spec.split()
            )
            
            if returncode == 0:
                return {
                    'success': True,
                    'message': f'Rule added successfully to {table}.{chain}'
                }
            else:
                return {
                    'success': False,
                    'error': stderr,
                    'message': f'Failed to add rule to {table}.{chain}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error adding iptables rule'
            }
    
    def insert_rule(self, table: str, chain: str, rule_number: int, rule_spec: str) -> Dict:
        """Belirtilen pozisyona kural ekle"""
        try:
            # Kural ekle
            returncode, stdout, stderr = self._run_command([
                'sudo', 'iptables', '-t', table, '-I', chain, str(rule_number)] + rule_spec.split()
            )
            
            if returncode == 0:
                return {
                    'success': True,
                    'message': f'Rule inserted successfully at position {rule_number} in {table}.{chain}'
                }
            else:
                return {
                    'success': False,
                    'error': stderr,
                    'message': f'Failed to insert rule at position {rule_number} in {table}.{chain}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error inserting iptables rule'
            }
    
    def get_chain_info(self, table: str, chain: str) -> Dict:
        """Belirtilen chain hakkında bilgi al"""
        try:
            # Chain bilgilerini al
            returncode, stdout, stderr = self._run_command([
                'sudo', 'iptables', '-t', table, '-L', chain, '-n', '-v'
            ])
            
            if returncode == 0:
                return {
                    'success': True,
                    'chain_info': stdout,
                    'message': f'Chain {chain} information retrieved successfully'
                }
            else:
                return {
                    'success': False,
                    'error': stderr,
                    'message': f'Failed to get chain {chain} information'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error getting chain information'
            }
    
    def parse_rule_line(self, line: str, table: str = 'filter', chain: str = 'INPUT') -> Optional[Dict]:
        """iptables kural satırını parse et"""
        # Boş satırları atla
        if not line.strip():
            return None
        
        # Chain başlıklarını atla
        if line.startswith('Chain '):
            return None
        
        # Header satırlarını atla
        if 'target' in line and 'prot' in line and 'source' in line:
            return None
        
        # Packet counter satırlarını atla
        if 'pkts' in line and 'bytes' in line:
            return None
        
        # Kural satırını parse et
        parts = line.split()
        if len(parts) < 2:
            return None
        
        # Kural numarasını kontrol et
        rule_number = None
        start_index = 0
        
        if parts[0].isdigit():
            rule_number = int(parts[0])
            start_index = 1
        
        if len(parts) < start_index + 2:
            return None
        
        rule = {
            'table': table,
            'chain': chain,  # Chain'i parametre olarak al
            'target': parts[start_index + 1],
            'protocol': 'any',
            'source': 'anywhere',
            'destination': 'anywhere',
            'port': 'any',
            'interface': 'any',
            'match': '',
            'options': '',
            'rule_number': rule_number
        }
        
        # Kalan parametreleri parse et
        i = start_index + 2
        while i < len(parts):
            part = parts[i]
            
            # Protocol
            if part in ['tcp', 'udp', 'icmp', 'all']:
                rule['protocol'] = part
            # Source IP
            elif part == '0.0.0.0/0' or part == 'anywhere':
                rule['source'] = 'anywhere'
            elif re.match(r'^\d+\.\d+\.\d+\.\d+', part):
                rule['source'] = part
            # Destination IP
            elif part == '0.0.0.0/0' or part == 'anywhere':
                rule['destination'] = 'anywhere'
            elif re.match(r'^\d+\.\d+\.\d+\.\d+', part):
                rule['destination'] = part
            # Port bilgisi
            elif 'dpt:' in part or 'spt:' in part:
                port_match = re.search(r'(dpt|spt):(\w+)', part)
                if port_match:
                    rule['port'] = port_match.group(2)
            # Interface bilgisi
            elif 'in:' in part or 'out:' in part:
                iface_match = re.search(r'(in|out):(\w+)', part)
                if iface_match:
                    rule['interface'] = iface_match.group(2)
            # Match modülleri
            elif any(part.startswith(prefix) for prefix in [
                'state', 'conntrack', 'multiport', 'limit', 'recent', 
                'mac', 'owner', 'time'
            ]):
                rule['match'] = part
            # Seçenekler ve parametreler
            elif part.startswith('--') or '=' in part or ':' in part:
                rule['options'] += (rule['options'] + ' ' if rule['options'] else '') + part
            
            i += 1
        
        # Seçenekleri temizle
        rule['options'] = rule['options'].strip()
        
        # Geçerli kural kontrolü
        if rule['chain'] == 'UNKNOWN' or rule['target'] == 'UNKNOWN':
            return None
        
        return rule

# ===== API FUNCTIONS =====

def api_iptables_status():
    """iptables durum API'si"""
    manager = IptablesManager()
    return manager.get_status()

def api_iptables_rules():
    """iptables kuralları API'si"""
    manager = IptablesManager()
    return manager.get_rules()

def api_iptables_delete_rule(table: str, chain: str, rule_number: int):
    """iptables kural silme API'si"""
    manager = IptablesManager()
    return manager.delete_rule(table, chain, rule_number)

def api_iptables_delete_rule_by_spec(table: str, chain: str, rule_spec: str):
    """iptables kural spesifikasyonuna göre silme API'si"""
    manager = IptablesManager()
    return manager.delete_rule_by_spec(table, chain, rule_spec)

def api_iptables_flush_chain(table: str, chain: str):
    """iptables chain temizleme API'si"""
    manager = IptablesManager()
    return manager.flush_chain(table, chain)

def api_iptables_add_rule(table: str, chain: str, rule_spec: str):
    """iptables kural ekleme API'si"""
    manager = IptablesManager()
    return manager.add_rule(table, chain, rule_spec)

def api_iptables_insert_rule(table: str, chain: str, rule_number: int, rule_spec: str):
    """iptables kural ekleme API'si (belirli pozisyona)"""
    manager = IptablesManager()
    return manager.insert_rule(table, chain, rule_number, rule_spec)

def api_iptables_get_chain_info(table: str, chain: str):
    """iptables chain bilgisi API'si"""
    manager = IptablesManager()
    return manager.get_chain_info(table, chain)
