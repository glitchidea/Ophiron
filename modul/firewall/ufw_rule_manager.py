"""
UFW Rule Management Module
Handles UFW rule creation, deletion, and management with flexible form
"""

import subprocess
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

class UFWRuleManager:
    """UFW Rule Management Class"""
    
    def __init__(self):
        pass
    
    def parse_port_input(self, port_input: str) -> List[str]:
        """
        Parse port input and return list of ports
        Supports:
        - Single port: "8080"
        - Multiple ports: "8080,8090,9000"
        - Port range: "8080:8090"
        - Mixed: "8080,8090:8100,9000"
        """
        if not port_input or not port_input.strip():
            return []
        
        ports = []
        port_input = port_input.strip()
        
        # Split by comma first
        for part in port_input.split(','):
            part = part.strip()
            if not part:
                continue
                
            if ':' in part:
                # Port range
                try:
                    start_port, end_port = part.split(':', 1)
                    start_port = int(start_port.strip())
                    end_port = int(end_port.strip())
                    
                    if start_port <= end_port:
                        for port in range(start_port, end_port + 1):
                            ports.append(str(port))
                    else:
                        logger.warning(f"Invalid port range: {part}")
                except ValueError:
                    logger.warning(f"Invalid port range format: {part}")
            else:
                # Single port
                try:
                    port = int(part)
                    if 1 <= port <= 65535:
                        ports.append(str(port))
                    else:
                        logger.warning(f"Port out of range: {port}")
                except ValueError:
                    logger.warning(f"Invalid port: {part}")
        
        return ports
    
    def parse_ip_input(self, ip_input: str) -> str:
        """
        Parse IP input and return validated IP or subnet
        Supports:
        - Single IP: "192.168.1.1"
        - Subnet: "192.168.1.0/24"
        - Any: "any" or empty
        """
        if not ip_input or ip_input.strip().lower() in ['any', '']:
            return 'any'
        
        ip_input = ip_input.strip()
        
        # Basic IP validation
        if '/' in ip_input:
            # CIDR notation
            ip, cidr = ip_input.split('/', 1)
            try:
                cidr_num = int(cidr)
                if 0 <= cidr_num <= 32:
                    return ip_input
            except ValueError:
                pass
        else:
            # Single IP
            if self._is_valid_ip(ip_input):
                return ip_input
        
        logger.warning(f"Invalid IP format: {ip_input}")
        return 'any'
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Basic IP validation"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except (ValueError, AttributeError):
            return False
    
    def build_ufw_command(self, rule_data: Dict[str, Any]) -> List[str]:
        """
        Build UFW command from rule data - flexible approach
        """
        action = rule_data.get('action', 'allow')
        direction = rule_data.get('direction', 'in')
        protocol = rule_data.get('protocol', 'tcp')
        source_ip = rule_data.get('source_ip', 'any')
        dest_ip = rule_data.get('dest_ip', 'any')
        ports = rule_data.get('ports', [])
        comment = rule_data.get('comment', '')
        
        # Build base command
        cmd = ['sudo', 'ufw', action]
        
        # Add direction if specified
        if direction and direction != 'any':
            cmd.append(direction)
        
        # Add protocol if specified and not 'any'
        if protocol and protocol != 'any':
            cmd.append('proto')
            cmd.append(protocol)
        
        # Add source IP if specified
        if source_ip and source_ip != 'any':
            cmd.append('from')
            cmd.append(source_ip)
        
        # Add destination IP if specified
        if dest_ip and dest_ip != 'any':
            cmd.append('to')
            cmd.append(dest_ip)
        
        # Add ports if specified
        if ports:
            cmd.append('port')
            if protocol and protocol != 'any':
                cmd.append(f"{ports[0]}/{protocol}")
            else:
                cmd.append(ports[0])
        
        # Add comment if specified
        if comment:
            cmd.extend(['comment', f'"{comment}"'])
        
        return cmd
    
    def create_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create UFW rule(s) based on rule data
        """
        try:
            # Parse inputs
            ports = self.parse_port_input(rule_data.get('ports', ''))
            source_ip = self.parse_ip_input(rule_data.get('source_ip', ''))
            dest_ip = self.parse_ip_input(rule_data.get('dest_ip', ''))
            
            created_rules = []
            errors = []
            
            if not ports:
                # No specific ports - create general rule
                rule_data['ports'] = []
                cmd = self.build_ufw_command(rule_data)
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    created_rules.append(' '.join(cmd))
                else:
                    error_msg = self.parse_ufw_error(result.stderr)
                    errors.append(f"Kural oluşturulamadı: {error_msg}")
            else:
                # Create rule for each port
                for port in ports:
                    rule_data_copy = rule_data.copy()
                    rule_data_copy['ports'] = [port]
                    cmd = self.build_ufw_command(rule_data_copy)
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        created_rules.append(' '.join(cmd))
                    else:
                        error_msg = self.parse_ufw_error(result.stderr)
                        errors.append(f"Port {port} için kural oluşturulamadı: {error_msg}")
            
            if created_rules:
                return {
                    'success': True,
                    'created_rules': created_rules,
                    'message': f"✅ {len(created_rules)} kural başarıyla oluşturuldu"
                }
            else:
                return {
                    'success': False,
                    'error': 'No rules created',
                    'message': '❌ Hiçbir kural oluşturulamadı',
                    'details': errors
                }
            
        except Exception as e:
            logger.error(f"Error creating UFW rule: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': '❌ Kural oluşturulurken beklenmeyen bir hata oluştu'
            }
    
    def delete_rule(self, rule_number: int) -> Dict[str, Any]:
        """
        Delete UFW rule by number using sudo
        """
        try:
            cmd = ['sudo', 'ufw', '--force', 'delete', str(rule_number)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'✅ Kural {rule_number} başarıyla silindi'
                }
            else:
                error_msg = self.parse_ufw_error(result.stderr)
                return {
                    'success': False,
                    'error': error_msg,
                    'message': f'❌ Kural {rule_number} silinemedi: {error_msg}'
                }
        except Exception as e:
            logger.error(f"Error deleting UFW rule: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': '❌ Kural silinirken beklenmeyen bir hata oluştu'
            }
    
    def get_rules(self) -> Dict[str, Any]:
        """
        Get all UFW rules with detailed information using sudo
        """
        try:
            result = subprocess.run(['sudo', 'ufw', 'status', 'numbered'], capture_output=True, text=True)
            
            if result.returncode == 0:
                rules = []
                output = result.stdout
                
                for line in output.split('\n'):
                    if '[' in line and ']' in line:
                        # Parse rule line
                        rule_info = self._parse_rule_line(line)
                        if rule_info:
                            rules.append(rule_info)
                
                return {
                    'success': True,
                    'rules': rules
                }
            else:
                error_msg = self.parse_ufw_error(result.stderr)
                return {
                    'success': False,
                    'error': f'UFW kuralları alınamadı: {error_msg}'
                }
        except Exception as e:
            logger.error(f"Error getting UFW rules: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_rule_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single UFW rule line
        """
        try:
            # Extract rule number
            rule_match = re.search(r'\[(\d+)\]', line)
            if not rule_match:
                return None
            
            rule_number = int(rule_match.group(1))
            
            # Parse rule content
            parts = line.split()
            if len(parts) < 2:
                return None
            
            action = parts[1] if len(parts) > 1 else 'Unknown'
            
            # Extract additional information
            rule_info = {
                'number': rule_number,
                'action': action,
                'raw_line': line.strip(),
                'from': '-',
                'to': '-',
                'port': '-',
                'protocol': '-',
                'comment': '-'
            }
            
            # Parse protocol, port, and other details
            for i, part in enumerate(parts[2:], 2):
                if part in ['tcp', 'udp', 'icmp']:
                    rule_info['protocol'] = part
                elif ':' in part and not part.startswith('['):
                    rule_info['port'] = part
                elif part.startswith('from'):
                    if i + 1 < len(parts):
                        rule_info['from'] = parts[i + 1]
                elif part.startswith('to'):
                    if i + 1 < len(parts):
                        rule_info['to'] = parts[i + 1]
                elif part.startswith('comment'):
                    # Extract comment (may contain spaces)
                    comment_parts = parts[i + 1:]
                    rule_info['comment'] = ' '.join(comment_parts).strip('"')
            
            return rule_info
            
        except Exception as e:
            logger.error(f"Error parsing rule line: {line} - {str(e)}")
            return None
    
    def parse_ufw_error(self, error_output: str) -> str:
        """
        Parse UFW error output and return user-friendly message
        """
        error_lower = error_output.lower()
        
        if 'permission denied' in error_lower:
            return 'Yetersiz yetki. Lütfen sudo ile çalıştırın.'
        elif 'invalid' in error_lower:
            return 'Geçersiz kural formatı. Lütfen parametreleri kontrol edin.'
        elif 'already exists' in error_lower:
            return 'Bu kural zaten mevcut.'
        elif 'not found' in error_lower:
            return 'Belirtilen kaynak bulunamadı.'
        elif 'bad port' in error_lower:
            return 'Geçersiz port numarası. Port 1-65535 arasında olmalıdır.'
        elif 'bad address' in error_lower:
            return 'Geçersiz IP adresi formatı.'
        elif 'bad protocol' in error_lower:
            return 'Geçersiz protokol. TCP, UDP, ICMP veya ANY kullanın.'
        elif 'bad action' in error_lower:
            return 'Geçersiz aksiyon. ALLOW, DENY veya REJECT kullanın.'
        else:
            return f'UFW hatası: {error_output.strip()}'

# Global instance
ufw_manager = UFWRuleManager()

# ===== API VIEWS =====

@csrf_exempt
@require_http_methods(["POST"])
def api_ufw_create_rule(request):
    """Create new UFW rule"""
    try:
        import json
        data = json.loads(request.body)
        
        result = ufw_manager.create_rule(data)
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        logger.error(f"Error in api_ufw_create_rule: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_http_methods(["DELETE"])
def api_ufw_delete_rule(request, rule_number):
    """Delete UFW rule by number"""
    try:
        rule_number = int(rule_number)
        result = ufw_manager.delete_rule(rule_number)
        return JsonResponse(result)
        
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid rule number'
        })
    except Exception as e:
        logger.error(f"Error in api_ufw_delete_rule: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_http_methods(["GET"])
def api_ufw_get_rules(request):
    """Get all UFW rules"""
    try:
        result = ufw_manager.get_rules()
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error in api_ufw_get_rules: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_http_methods(["GET"])
def api_ufw_rule_form_data(request):
    """Get form data for UFW rule creation"""
    try:
        form_data = {
            'actions': ['allow', 'deny', 'reject'],
            'directions': ['in', 'out', 'any'],
            'protocols': ['tcp', 'udp', 'icmp', 'any'],
            'examples': {
                'ports': [
                    '8080 - Single port',
                    '8080,8090 - Multiple ports',
                    '8080:8090 - Port range',
                    '8080,8090:8100,9000 - Mixed'
                ],
                'ips': [
                    '192.168.1.1 - Single IP',
                    '192.168.1.0/24 - Subnet',
                    'any - Any IP'
                ]
            }
        }
        
        return JsonResponse({
            'success': True,
            'form_data': form_data
        })
        
    except Exception as e:
        logger.error(f"Error in api_ufw_rule_form_data: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })