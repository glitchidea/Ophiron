"""
Service Builder utility functions
Linux systemd service management utilities
"""
import os
import subprocess
import socket
import psutil
import pwd
import grp
import logging
import re
from pathlib import Path
from .models import ServiceLog

logger = logging.getLogger(__name__)

# Service manager detection and operations
def detect_service_manager():
    """Detect available service manager on the system"""
    service_managers = []
    
    # Check for systemd
    if subprocess.run(['which', 'systemctl'], capture_output=True).returncode == 0:
        service_managers.append('systemd')
    
    # Check for sysvinit
    if os.path.exists('/etc/init.d') and os.path.exists('/etc/rc.d'):
        service_managers.append('sysvinit')
    
    # Check for upstart
    if subprocess.run(['which', 'initctl'], capture_output=True).returncode == 0:
        service_managers.append('upstart')
    
    # Check for openrc
    if subprocess.run(['which', 'rc-service'], capture_output=True).returncode == 0:
        service_managers.append('openrc')
    
    # Check for runit
    if subprocess.run(['which', 'sv'], capture_output=True).returncode == 0:
        service_managers.append('runit')
    
    return service_managers

def get_primary_service_manager():
    """Get the primary service manager (prefer systemd)"""
    managers = detect_service_manager()
    
    # Priority order: systemd > openrc > upstart > sysvinit > runit
    priority_order = ['systemd', 'openrc', 'upstart', 'sysvinit', 'runit']
    
    for manager in priority_order:
        if manager in managers:
            return manager
    
    return managers[0] if managers else 'unknown'

# Service manager operations
class ServiceManager:
    """Abstract service manager operations"""
    
    @staticmethod
    def create_service(service_config, manager_type=None):
        """Create service using the specified manager"""
        if manager_type is None:
            manager_type = get_primary_service_manager()
        
        if manager_type == 'systemd':
            return create_systemd_service(service_config)
        elif manager_type == 'sysvinit':
            return create_sysvinit_service(service_config)
        elif manager_type == 'upstart':
            return create_upstart_service(service_config)
        elif manager_type == 'openrc':
            return create_openrc_service(service_config)
        elif manager_type == 'runit':
            return create_runit_service(service_config)
        else:
            return False, f"Unsupported service manager: {manager_type}"
    
    @staticmethod
    def update_service(service_config, manager_type=None):
        """Update service using the specified manager"""
        if manager_type is None:
            manager_type = get_primary_service_manager()
        
        if manager_type == 'systemd':
            return update_systemd_service(service_config)
        elif manager_type == 'sysvinit':
            return update_sysvinit_service(service_config)
        elif manager_type == 'upstart':
            return update_upstart_service(service_config)
        elif manager_type == 'openrc':
            return update_openrc_service(service_config)
        elif manager_type == 'runit':
            return update_runit_service(service_config)
        else:
            return False, f"Unsupported service manager: {manager_type}"
    
    @staticmethod
    def delete_service(service_name, manager_type=None):
        """Delete service using the specified manager"""
        if manager_type is None:
            manager_type = get_primary_service_manager()
        
        if manager_type == 'systemd':
            return delete_systemd_service(service_name)
        elif manager_type == 'sysvinit':
            return delete_sysvinit_service(service_name)
        elif manager_type == 'upstart':
            return delete_upstart_service(service_name)
        elif manager_type == 'openrc':
            return delete_openrc_service(service_name)
        elif manager_type == 'runit':
            return delete_runit_service(service_name)
        else:
            return False, f"Unsupported service manager: {manager_type}"
    
    @staticmethod
    def get_service_status(service_name, manager_type=None):
        """Get service status using the specified manager"""
        if manager_type is None:
            manager_type = get_primary_service_manager()
        
        if manager_type == 'systemd':
            return get_systemd_service_status(service_name)
        elif manager_type == 'sysvinit':
            return get_sysvinit_service_status(service_name)
        elif manager_type == 'upstart':
            return get_upstart_service_status(service_name)
        elif manager_type == 'openrc':
            return get_openrc_service_status(service_name)
        elif manager_type == 'runit':
            return get_runit_service_status(service_name)
        else:
            return {'status': 'unknown', 'message': f'Unsupported service manager: {manager_type}'}
    
    @staticmethod
    def control_service(service_name, action, manager_type=None):
        """Control service using the specified manager"""
        if manager_type is None:
            manager_type = get_primary_service_manager()
        
        if manager_type == 'systemd':
            return control_systemd_service(service_name, action)
        elif manager_type == 'sysvinit':
            return control_sysvinit_service(service_name, action)
        elif manager_type == 'upstart':
            return control_upstart_service(service_name, action)
        elif manager_type == 'openrc':
            return control_openrc_service(service_name, action)
        elif manager_type == 'runit':
            return control_runit_service(service_name, action)
        else:
            return False, f"Unsupported service manager: {manager_type}"


def validate_application_path(app_path, app_type='normal'):
    """
    Validate application path and return final executable path
    """
    try:
        # Clean path
        app_path = app_path.strip().strip('"\'')
        app_path = os.path.abspath(app_path)
        
        # Check if file exists
        if not os.path.exists(app_path):
            return False, f"File not found: {app_path}", None
        
        # Check if file is readable
        if not os.access(app_path, os.R_OK):
            return False, f"No read permission: {app_path}", None
        
        # For Python files, check if executable or needs interpreter
        if app_path.endswith('.py'):
            if os.access(app_path, os.X_OK):
                return True, "Python file is executable", f'"{app_path}"'
            else:
                # Find Python interpreter
                python_path = find_python_interpreter()
                if python_path:
                    return True, "Python file needs interpreter", f'{python_path} "{app_path}"'
                else:
                    return False, "Python interpreter not found", None
        else:
            # Check if file is executable
            if os.access(app_path, os.X_OK):
                return True, "File is executable", f'"{app_path}"'
            else:
                return False, f"File is not executable: {app_path}", None
                
    except Exception as e:
        logger.error(f"Error validating path: {e}")
        return False, f"Path validation error: {str(e)}", None


def find_python_interpreter():
    """Find Python interpreter path"""
    try:
        # Try python3 first
        result = subprocess.run(['which', 'python3'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        
        # Try python
        result = subprocess.run(['which', 'python'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        
        # Try common paths
        common_paths = [
            '/usr/bin/python3',
            '/usr/local/bin/python3',
            '/usr/bin/python',
            '/usr/local/bin/python'
        ]
        
        for path in common_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
                
        return None
        
    except Exception as e:
        logger.error(f"Error finding Python interpreter: {e}")
        return None


def check_port_availability(port):
    """Check if port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            return result != 0  # Port is available if connection fails
    except Exception as e:
        logger.error(f"Error checking port: {e}")
        return False


def suggest_service_config(app_path, app_type='normal'):
    """Suggest service configuration based on application path"""
    suggestions = {
        'interpreter': None,
        'user': None,
        'working_directory': None,
        'port': None,
        'host': '0.0.0.0'
    }
    
    try:
        # Get working directory
        suggestions['working_directory'] = os.path.dirname(os.path.abspath(app_path))
        
        # Get current user
        current_user = os.getenv('USER', 'root')
        suggestions['user'] = current_user
        
        # For Python files, suggest interpreter
        if app_path.endswith('.py'):
            suggestions['interpreter'] = find_python_interpreter()
        
        # For web applications, suggest common ports
        if app_type == 'web':
            suggestions['port'] = 8080
            suggestions['host'] = '0.0.0.0'
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Error suggesting config: {e}")
        return suggestions


def analyze_python_file(file_path):
    """Analyze Python file for port and host configuration"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        port = None
        host = None
        
        # Port patterns
        port_patterns = [
            r'port\s*=\s*(\d+)',
            r'\.run\(.*port\s*=\s*(\d+)',
            r'\.run\(.*:(\d+)',
            r'PORT\s*=\s*(\d+)',
            r'listen\(.*?(\d+)\)',
        ]
        
        # Host patterns
        host_patterns = [
            r'host\s*=\s*[\'"](.+?)[\'"]',
            r'\.run\(.*host\s*=\s*[\'"](.+?)[\'"]',
            r'HOST\s*=\s*[\'"](.+?)[\'"]',
            r'listen\([\'"](.+?)[\'"]',
        ]
        
        # Find port
        for pattern in port_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                port = int(match.group(1))
                break
        
        # Find host
        for pattern in host_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                host = match.group(1)
                break
        
        return {
            'port': port,
            'host': host,
            'available_hosts': ['0.0.0.0', '127.0.0.1', 'localhost'] + get_local_ips()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing Python file: {e}")
        return {'port': None, 'host': None, 'available_hosts': []}


def get_local_ips():
    """Get local IP addresses"""
    ips = []
    try:
        for interface in psutil.net_if_addrs():
            for addr in psutil.net_if_addrs()[interface]:
                if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                    ips.append(addr.address)
    except Exception as e:
        logger.error(f"Error getting local IPs: {e}")
    return ips


def create_systemd_service(service_config):
    """Create systemd service file with proper sudo permissions"""
    try:
        service_name = service_config.name
        service_file_path = f"/etc/systemd/system/{service_name}.service"
        
        # Build service content
        service_content = [
            "[Unit]",
            f"Description={service_config.description or service_name}",
            "After=network.target",
            "",
            "[Service]",
            "Type=simple",
            f"User={service_config.user}"
        ]
        
        # Add working directory if specified
        if service_config.working_directory:
            service_content.append(f"WorkingDirectory={service_config.working_directory}")
        
        # Add environment variables
        if service_config.environment_vars:
            for line in service_config.environment_vars.split('\n'):
                if '=' in line:
                    service_content.append(f"Environment={line.strip()}")
        
        # Add port and host environment variables
        if service_config.port:
            service_content.append(f"Environment=PORT={service_config.port}")
        if service_config.host:
            service_content.append(f"Environment=HOST={service_config.host}")
        
        # Add ExecStart
        if service_config.interpreter:
            service_content.append(f'ExecStart={service_config.interpreter} "{service_config.application_path}"')
        else:
            service_content.append(f'ExecStart="{service_config.application_path}"')
        
        # Add restart policy
        service_content.extend([
            f"Restart={service_config.restart_policy}",
            "RestartSec=5",
            "",
            "[Install]",
            "WantedBy=multi-user.target"
        ])
        
        # Create service content as string
        service_content_str = '\n'.join(service_content)
        
        # Write service file using sudo
        write_result = subprocess.run([
            'sudo', 'tee', service_file_path
        ], input=service_content_str, text=True, capture_output=True)
        
        if write_result.returncode != 0:
            return False, f"Failed to write service file: {write_result.stderr}"
        
        # Set permissions using sudo
        chmod_result = subprocess.run([
            'sudo', 'chmod', '644', service_file_path
        ], capture_output=True, text=True)
        
        if chmod_result.returncode != 0:
            return False, f"Failed to set permissions: {chmod_result.stderr}"
        
        # Reload systemd and enable service using sudo
        daemon_reload = subprocess.run([
            'sudo', 'systemctl', 'daemon-reload'
        ], capture_output=True, text=True)
        
        if daemon_reload.returncode != 0:
            return False, f"Failed to reload systemd: {daemon_reload.stderr}"
        
        # Enable service
        enable_result = subprocess.run([
            'sudo', 'systemctl', 'enable', f'{service_name}.service'
        ], capture_output=True, text=True)
        
        if enable_result.returncode != 0:
            return False, f"Failed to enable service: {enable_result.stderr}"
        
        # Start service
        start_result = subprocess.run([
            'sudo', 'systemctl', 'start', f'{service_name}.service'
        ], capture_output=True, text=True)
        
        if start_result.returncode != 0:
            return False, f"Failed to start service: {start_result.stderr}"
        
        return True, f"Service {service_name} created and started successfully"
        
    except Exception as e:
        logger.error(f"Error creating systemd service: {e}")
        return False, f"Error creating service: {str(e)}"


def get_system_users():
    """Get system users for service configuration"""
    users = []
    try:
        for user in pwd.getpwall():
            # Only include regular users (UID >= 1000) and system users like www-data
            if user.pw_uid >= 1000 or user.pw_name in ['www-data', 'nginx', 'apache']:
                users.append(user.pw_name)
    except Exception as e:
        logger.error(f"Error getting system users: {e}")
        # Fallback to current user
        users = [os.getenv('USER', 'root')]
    return users


def get_network_interfaces():
    """Get network interfaces"""
    interfaces = []
    try:
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    interfaces.append({
                        'name': interface,
                        'ip': addr.address,
                        'netmask': addr.netmask
                    })
    except Exception as e:
        logger.error(f"Error getting network interfaces: {e}")
    return interfaces


def log_service_operation(service_name, action, status, message, user='Anonymous', ip_address=None, details=None):
    """Log service operation"""
    try:
        ServiceLog.objects.create(
            service_name=service_name,
            action=action,
            status=status,
            message=message,
            user=user,
            ip_address=ip_address,
            details=details
        )
    except Exception as e:
        logger.error(f"Failed to log service operation: {e}")


def get_service_status(service_name):
    """Get service status from systemd"""
    try:
        result = subprocess.run(
            ['sudo', 'systemctl', 'status', f'{service_name}.service'],
            capture_output=True,
            text=True
        )
        
        if 'Active: active (running)' in result.stdout:
            return {'status': 'running', 'message': 'Service is running'}
        elif 'Active: inactive (dead)' in result.stdout:
            return {'status': 'stopped', 'message': 'Service is stopped'}
        else:
            return {'status': 'unknown', 'message': result.stdout}
            
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def control_service(service_name, action):
    """Control service (start, stop, restart, enable, disable)"""
    try:
        if action in ['start', 'stop', 'restart', 'enable', 'disable']:
            result = subprocess.run(
                ['sudo', 'systemctl', action, f'{service_name}.service'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, f"Service {action} successful"
            else:
                return False, f"Service {action} failed: {result.stderr}"
        else:
            return False, f"Invalid action: {action}"
            
    except Exception as e:
        return False, f"Error controlling service: {str(e)}"


def update_systemd_service(service_config):
    """Update systemd service file"""
    try:
        service_name = service_config.name
        service_file_path = f"/etc/systemd/system/{service_name}.service"
        
        # Stop service first
        stop_result = subprocess.run(
            ['systemctl', 'stop', f'{service_name}.service'],
            capture_output=True,
            text=True
        )
        
        # Build new service content
        service_content = [
            "[Unit]",
            f"Description={service_config.description or service_name}",
            "After=network.target",
            "",
            "[Service]",
            "Type=simple",
            f"User={service_config.user}"
        ]
        
        # Add working directory if specified
        if service_config.working_directory:
            service_content.append(f"WorkingDirectory={service_config.working_directory}")
        
        # Add environment variables
        if service_config.environment_vars:
            for line in service_config.environment_vars.split('\n'):
                if '=' in line:
                    service_content.append(f"Environment={line.strip()}")
        
        # Add port and host environment variables
        if service_config.port:
            service_content.append(f"Environment=PORT={service_config.port}")
        if service_config.host:
            service_content.append(f"Environment=HOST={service_config.host}")
        
        # Add ExecStart
        if service_config.interpreter:
            service_content.append(f'ExecStart={service_config.interpreter} "{service_config.application_path}"')
        else:
            service_content.append(f'ExecStart="{service_config.application_path}"')
        
        # Add restart policy
        service_content.extend([
            f"Restart={service_config.restart_policy}",
            "RestartSec=5",
            "",
            "[Install]",
            "WantedBy=multi-user.target"
        ])
        
        # Create service content as string
        service_content_str = '\n'.join(service_content)
        
        # Write updated service file using sudo
        write_result = subprocess.run([
            'sudo', 'tee', service_file_path
        ], input=service_content_str, text=True, capture_output=True)
        
        if write_result.returncode != 0:
            return False, f"Failed to update service file: {write_result.stderr}"
        
        # Set permissions using sudo
        chmod_result = subprocess.run([
            'sudo', 'chmod', '644', service_file_path
        ], capture_output=True, text=True)
        
        if chmod_result.returncode != 0:
            return False, f"Failed to set permissions: {chmod_result.stderr}"
        
        # Reload systemd
        reload_result = subprocess.run([
            'sudo', 'systemctl', 'daemon-reload'
        ], capture_output=True, text=True)
        
        if reload_result.returncode != 0:
            return False, f"Failed to reload systemd: {reload_result.stderr}"
        
        # Enable service
        enable_result = subprocess.run([
            'sudo', 'systemctl', 'enable', f'{service_name}.service'
        ], capture_output=True, text=True)
        
        if enable_result.returncode != 0:
            return False, f"Failed to enable service: {enable_result.stderr}"
        
        # Start service
        start_result = subprocess.run([
            'sudo', 'systemctl', 'start', f'{service_name}.service'
        ], capture_output=True, text=True)
        
        if start_result.returncode != 0:
            return False, f"Failed to start service: {start_result.stderr}"
        
        return True, f"Service {service_name} updated successfully"
        
    except Exception as e:
        logger.error(f"Error updating systemd service: {e}")
        return False, f"Error updating service: {str(e)}"


def delete_systemd_service(service_name):
    """Delete systemd service completely"""
    try:
        service_file_path = f"/etc/systemd/system/{service_name}.service"
        
        # Stop service first
        stop_result = subprocess.run(
            ['sudo', 'systemctl', 'stop', f'{service_name}.service'],
            capture_output=True,
            text=True
        )
        
        # Disable service
        disable_result = subprocess.run(
            ['sudo', 'systemctl', 'disable', f'{service_name}.service'],
            capture_output=True,
            text=True
        )
        
        # Remove service file
        remove_result = subprocess.run(
            ['sudo', 'rm', '-f', service_file_path],
            capture_output=True,
            text=True
        )
        
        if remove_result.returncode != 0:
            return False, f"Failed to remove service file: {remove_result.stderr}"
        
        # Reload systemd
        reload_result = subprocess.run(
            ['sudo', 'systemctl', 'daemon-reload'],
            capture_output=True,
            text=True
        )
        
        if reload_result.returncode != 0:
            return False, f"Failed to reload systemd: {reload_result.stderr}"
        
        return True, f"Service {service_name} deleted successfully"
        
    except Exception as e:
        logger.error(f"Error deleting systemd service: {e}")
        return False, f"Error deleting service: {str(e)}"

# SysV Init Service Operations
def create_sysvinit_service(service_config):
    """Create SysV init service"""
    try:
        service_name = service_config.name
        service_file_path = f"/etc/init.d/{service_name}"
        
        # Create init script content
        init_script = f"""#!/bin/bash
### BEGIN INIT INFO
# Provides:          {service_name}
# Required-Start:    $local_fs $network
# Required-Stop:     $local_fs $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: {service_config.description}
# Description:       {service_config.description}
### END INIT INFO

SERVICE_NAME="{service_name}"
SERVICE_USER="{service_config.user}"
SERVICE_DIR="{service_config.working_directory}"
SERVICE_CMD="{service_config.application_path}"

case "$1" in
    start)
        echo "Starting $SERVICE_NAME..."
        cd $SERVICE_DIR
        su - $SERVICE_USER -c "$SERVICE_CMD" &
        echo $! > /var/run/$SERVICE_NAME.pid
        ;;
    stop)
        echo "Stopping $SERVICE_NAME..."
        if [ -f /var/run/$SERVICE_NAME.pid ]; then
            kill $(cat /var/run/$SERVICE_NAME.pid)
            rm -f /var/run/$SERVICE_NAME.pid
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if [ -f /var/run/$SERVICE_NAME.pid ]; then
            if kill -0 $(cat /var/run/$SERVICE_NAME.pid) 2>/dev/null; then
                echo "$SERVICE_NAME is running"
                exit 0
            else
                echo "$SERVICE_NAME is not running"
                exit 1
            fi
        else
            echo "$SERVICE_NAME is not running"
            exit 1
        fi
        ;;
    *)
        echo "Usage: $0 {{start|stop|restart|status}}"
        exit 1
        ;;
esac
"""
        
        # Write init script using sudo
        write_result = subprocess.run([
            'sudo', 'tee', service_file_path
        ], input=init_script, text=True, capture_output=True)
        
        if write_result.returncode != 0:
            return False, f"Failed to write init script: {write_result.stderr}"
        
        # Set permissions using sudo
        chmod_result = subprocess.run([
            'sudo', 'chmod', '+x', service_file_path
        ], capture_output=True, text=True)
        
        if chmod_result.returncode != 0:
            return False, f"Failed to set permissions: {chmod_result.stderr}"
        
        # Enable service (create symlinks)
        for runlevel in ['2', '3', '4', '5']:
            symlink_result = subprocess.run([
                'sudo', 'ln', '-sf', service_file_path, f'/etc/rc{runlevel}.d/S99{service_name}'
            ], capture_output=True, text=True)
        
        return True, f"SysV init service {service_name} created successfully"
        
    except Exception as e:
        logger.error(f"Error creating SysV init service: {e}")
        return False, f"Error creating service: {str(e)}"

def update_sysvinit_service(service_config):
    """Update SysV init service"""
    return create_sysvinit_service(service_config)  # Same as create for SysV

def delete_sysvinit_service(service_name):
    """Delete SysV init service"""
    try:
        service_file_path = f"/etc/init.d/{service_name}"
        
        # Stop service first
        subprocess.run(['sudo', 'service', service_name, 'stop'], capture_output=True)
        
        # Remove symlinks
        for runlevel in ['0', '1', '2', '3', '4', '5', '6']:
            subprocess.run(['sudo', 'rm', '-f', f'/etc/rc{runlevel}.d/*{service_name}'], capture_output=True)
        
        # Remove init script
        remove_result = subprocess.run([
            'sudo', 'rm', '-f', service_file_path
        ], capture_output=True, text=True)
        
        if remove_result.returncode != 0:
            return False, f"Failed to remove init script: {remove_result.stderr}"
        
        return True, f"SysV init service {service_name} deleted successfully"
        
    except Exception as e:
        logger.error(f"Error deleting SysV init service: {e}")
        return False, f"Error deleting service: {str(e)}"

def get_sysvinit_service_status(service_name):
    """Get SysV init service status"""
    try:
        result = subprocess.run(
            ['sudo', 'service', service_name, 'status'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return {'status': 'running', 'message': 'Service is running'}
        else:
            return {'status': 'stopped', 'message': 'Service is stopped'}
            
    except Exception as e:
        return {'status': 'error', 'message': f'Error checking status: {str(e)}'}

def control_sysvinit_service(service_name, action):
    """Control SysV init service"""
    try:
        if action in ['start', 'stop', 'restart']:
            result = subprocess.run(
                ['sudo', 'service', service_name, action],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, f"Service {action} successful"
            else:
                return False, f"Service {action} failed: {result.stderr}"
        else:
            return False, f"Unsupported action: {action}"
            
    except Exception as e:
        logger.error(f"Error controlling SysV init service: {e}")
        return False, f"Error controlling service: {str(e)}"

# OpenRC Service Operations
def create_openrc_service(service_config):
    """Create OpenRC service"""
    try:
        service_name = service_config.name
        service_file_path = f"/etc/init.d/{service_name}"
        
        # Create OpenRC init script
        init_script = f"""#!/sbin/openrc-run
# Copyright 1999-2019 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

description="{service_config.description}"
command="{service_config.application_path}"
command_user="{service_config.user}"
command_background="yes"
pidfile="/var/run/${{RC_SVCNAME}}.pid"
start_stop_daemon_args="--chdir {service_config.working_directory}"

depend() {{
    need localmount
    after localmount
}}
"""
        
        # Write init script using sudo
        write_result = subprocess.run([
            'sudo', 'tee', service_file_path
        ], input=init_script, text=True, capture_output=True)
        
        if write_result.returncode != 0:
            return False, f"Failed to write OpenRC script: {write_result.stderr}"
        
        # Set permissions using sudo
        chmod_result = subprocess.run([
            'sudo', 'chmod', '+x', service_file_path
        ], capture_output=True, text=True)
        
        if chmod_result.returncode != 0:
            return False, f"Failed to set permissions: {chmod_result.stderr}"
        
        # Add service to default runlevel
        add_result = subprocess.run([
            'sudo', 'rc-update', 'add', service_name, 'default'
        ], capture_output=True, text=True)
        
        if add_result.returncode != 0:
            return False, f"Failed to add service to default runlevel: {add_result.stderr}"
        
        return True, f"OpenRC service {service_name} created successfully"
        
    except Exception as e:
        logger.error(f"Error creating OpenRC service: {e}")
        return False, f"Error creating service: {str(e)}"

def update_openrc_service(service_config):
    """Update OpenRC service"""
    return create_openrc_service(service_config)  # Same as create for OpenRC

def delete_openrc_service(service_name):
    """Delete OpenRC service"""
    try:
        service_file_path = f"/etc/init.d/{service_name}"
        
        # Stop service first
        subprocess.run(['sudo', 'rc-service', service_name, 'stop'], capture_output=True)
        
        # Remove from runlevels
        subprocess.run(['sudo', 'rc-update', 'del', service_name], capture_output=True)
        
        # Remove init script
        remove_result = subprocess.run([
            'sudo', 'rm', '-f', service_file_path
        ], capture_output=True, text=True)
        
        if remove_result.returncode != 0:
            return False, f"Failed to remove OpenRC script: {remove_result.stderr}"
        
        return True, f"OpenRC service {service_name} deleted successfully"
        
    except Exception as e:
        logger.error(f"Error deleting OpenRC service: {e}")
        return False, f"Error deleting service: {str(e)}"

def get_openrc_service_status(service_name):
    """Get OpenRC service status"""
    try:
        result = subprocess.run(
            ['sudo', 'rc-service', service_name, 'status'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return {'status': 'running', 'message': 'Service is running'}
        else:
            return {'status': 'stopped', 'message': 'Service is stopped'}
            
    except Exception as e:
        return {'status': 'error', 'message': f'Error checking status: {str(e)}'}

def control_openrc_service(service_name, action):
    """Control OpenRC service"""
    try:
        if action in ['start', 'stop', 'restart']:
            result = subprocess.run(
                ['sudo', 'rc-service', service_name, action],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, f"Service {action} successful"
            else:
                return False, f"Service {action} failed: {result.stderr}"
        elif action in ['enable', 'disable']:
            if action == 'enable':
                result = subprocess.run(
                    ['sudo', 'rc-update', 'add', service_name],
                    capture_output=True,
                    text=True
                )
            else:
                result = subprocess.run(
                    ['sudo', 'rc-update', 'del', service_name],
                    capture_output=True,
                    text=True
                )
            
            if result.returncode == 0:
                return True, f"Service {action} successful"
            else:
                return False, f"Service {action} failed: {result.stderr}"
        else:
            return False, f"Unsupported action: {action}"
            
    except Exception as e:
        logger.error(f"Error controlling OpenRC service: {e}")
        return False, f"Error controlling service: {str(e)}"
