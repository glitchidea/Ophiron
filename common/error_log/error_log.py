"""
Ophiron Security Logging System
Writes security logs to logger/error-login/ directory
"""

import os
import json
import logging
from datetime import datetime
from django.conf import settings
from django.http import HttpRequest

# Log directory path (moved from logger/error-login to logger/security)
LOG_DIR = os.path.join(settings.BASE_DIR, 'logger', 'security')

# Create new log directory and migrate legacy file if present
os.makedirs(LOG_DIR, exist_ok=True)

# Backward-compat: move legacy security.log if it exists under error-login
_LEGACY_DIR = os.path.join(settings.BASE_DIR, 'logger', 'error-login')
_LEGACY_FILE = os.path.join(_LEGACY_DIR, 'security.log')
_NEW_FILE = os.path.join(LOG_DIR, 'security.log')
try:
    if os.path.isfile(_LEGACY_FILE) and not os.path.exists(_NEW_FILE):
        # Attempt atomic rename; if cross-device fails, fallback to copy
        try:
            os.replace(_LEGACY_FILE, _NEW_FILE)
        except Exception:
            with open(_LEGACY_FILE, 'rb') as src, open(_NEW_FILE, 'ab') as dst:
                dst.write(src.read())
            # keep legacy file to avoid breaking external processes
except Exception:
    pass

# Logger configuration
def setup_security_logger():
    """Configure security logger"""
    logger = logging.getLogger('ophiron_security')
    logger.setLevel(logging.INFO)
    
    # If handlers already exist, clear them
    if logger.handlers:
        logger.handlers.clear()
    
    # File handler
    log_file = os.path.join(LOG_DIR, 'security.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    return logger

# Global logger instance
security_logger = setup_security_logger()

def get_user_agent(request: HttpRequest) -> str:
    """Get User-Agent string"""
    return request.META.get('HTTP_USER_AGENT', 'Unknown')

def get_device_info(user_agent: str) -> dict:
    """Extract basic device info from User-Agent"""
    device_info = {
        'browser': 'Unknown',
        'os': 'Unknown',
        'device_type': 'Unknown'
    }
    
    # Basic browser detection
    if 'Chrome' in user_agent:
        device_info['browser'] = 'Chrome'
    elif 'Firefox' in user_agent:
        device_info['browser'] = 'Firefox'
    elif 'Safari' in user_agent:
        device_info['browser'] = 'Safari'
    elif 'Edge' in user_agent:
        device_info['browser'] = 'Edge'
    
    # OS detection
    if 'Windows' in user_agent:
        device_info['os'] = 'Windows'
    elif 'Mac' in user_agent:
        device_info['os'] = 'macOS'
    elif 'Linux' in user_agent:
        device_info['os'] = 'Linux'
    elif 'Android' in user_agent:
        device_info['os'] = 'Android'
    elif 'iOS' in user_agent:
        device_info['os'] = 'iOS'
    
    # Device type detection
    if 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent:
        device_info['device_type'] = 'Mobile'
    elif 'Tablet' in user_agent or 'iPad' in user_agent:
        device_info['device_type'] = 'Tablet'
    else:
        device_info['device_type'] = 'Desktop'
    
    return device_info

def log_login_attempt(request: HttpRequest, username: str, success: bool, failure_reason: str = ''):
    """
    Log a login attempt
    
    Args:
        request: Django HttpRequest object
        username: Attempted username
        success: Whether login succeeded
        failure_reason: Reason for failure
    """
    try:
        # Basic info
        user_agent = get_user_agent(request)
        device_info = get_device_info(user_agent)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Log data
        log_data = {
            'timestamp': timestamp,
            'user_agent': user_agent,
            'username_attempted': username,
            'login_success': success,
            'failure_reason': failure_reason,
            'device_info': device_info,
            'session_id': request.session.session_key or 'No Session',
            'referrer': request.META.get('HTTP_REFERER', 'Direct'),
            'request_method': request.method,
            'request_path': request.path
        }
        
        # Serialize to JSON for logging
        log_message = json.dumps(log_data, ensure_ascii=False, indent=2)
        
        # Log level
        log_level = logging.INFO if success else logging.WARNING
        
        # Write to logger
        security_logger.log(log_level, f"LOGIN_ATTEMPT: {log_message}")
        
        # Also append to daily log file
        daily_log_file = os.path.join(LOG_DIR, f"security_{datetime.now().strftime('%Y-%m-%d')}.log")
        with open(daily_log_file, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} - {'SUCCESS' if success else 'FAILED'} - {username}\n")
        
        return True
        
    except Exception as e:
        # On logging error
        security_logger.error(f"LOG_ERROR: Failed to log security event: {str(e)}")
        return False

def log_security_event(event_type: str, request: HttpRequest, details: dict = None):
    """
    Log a general security event
    
    Args:
        event_type: Event type (LOGIN_FAILED, SUSPICIOUS_ACTIVITY, etc.)
        request: Django HttpRequest object
        details: Extra details
    """
    try:
        user_agent = get_user_agent(request)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        log_data = {
            'timestamp': timestamp,
            'event_type': event_type,
            'user_agent': user_agent,
            'details': details or {},
            'session_id': request.session.session_key or 'No Session'
        }
        
        log_message = json.dumps(log_data, ensure_ascii=False, indent=2)
        security_logger.warning(f"SECURITY_EVENT: {log_message}")
        
        return True
        
    except Exception as e:
        security_logger.error(f"LOG_ERROR: Failed to log security event: {str(e)}")
        return False

def get_recent_logs(hours: int = 24) -> list:
    """
    Get logs in the last N hours
    
    Args:
        hours: How many hours back to look
    
    Returns:
        List of log entries
    """
    try:
        log_file = os.path.join(LOG_DIR, 'security.log')
        if not os.path.exists(log_file):
            return []
        
        logs = []
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if 'LOGIN_ATTEMPT:' in line:
                    try:
                        # Extract JSON part
                        json_start = line.find('LOGIN_ATTEMPT: ') + len('LOGIN_ATTEMPT: ')
                        json_data = line[json_start:].strip()
                        log_entry = json.loads(json_data)
                        
                        # Time filter
                        log_time = datetime.strptime(log_entry['timestamp'], '%Y-%m-%d %H:%M:%S')
                        if log_time.timestamp() >= cutoff_time:
                            logs.append(log_entry)
                    except:
                        continue
        
        return logs
        
    except Exception as e:
        security_logger.error(f"LOG_ERROR: Failed to get recent logs: {str(e)}")
        return []

def cleanup_old_logs(days: int = 30):
    """
    Clean up old logs
    
    Args:
        days: Delete logs older than this many days
    """
    try:
        cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)
        
        for filename in os.listdir(LOG_DIR):
            if filename.startswith('security_') and filename.endswith('.log'):
                file_path = os.path.join(LOG_DIR, filename)
                if os.path.getmtime(file_path) < cutoff_date:
                    os.remove(file_path)
                    security_logger.info(f"Cleaned up old log file: {filename}")
        
        return True
        
    except Exception as e:
        security_logger.error(f"LOG_ERROR: Failed to cleanup old logs: {str(e)}")
        return False
