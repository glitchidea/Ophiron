import os
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Iterable


class LogReader:
    def read_logs(self) -> Dict[str, List[str]]:
        raise NotImplementedError


class FileLogReader(LogReader):
    def __init__(self, file_map: Optional[Dict[str, str]] = None, fallback_dir: Optional[str] = None, lines: int = 1000):
        self.file_map = file_map or {}
        self.fallback_dir = fallback_dir
        self.lines = lines
        # Common log files in Linux systems
        self.common_log_paths = {
            'system': ['/var/log/syslog', '/var/log/messages', '/var/log/system.log'],
            'kernel': ['/var/log/kern.log', '/var/log/kernel.log', '/var/log/dmesg'],
            'auth': ['/var/log/auth.log', '/var/log/secure', '/var/log/audit/audit.log'],
            'daemon': ['/var/log/daemon.log', '/var/log/service.log'],
            'boot': ['/var/log/boot.log', '/var/log/boot'],
            'cron': ['/var/log/cron.log', '/var/log/cron', '/var/log/crond.log'],
            'mail': ['/var/log/mail.log', '/var/log/maillog'],
            'apache': ['/var/log/apache2/access.log', '/var/log/httpd/access_log'],
            'nginx': ['/var/log/nginx/access.log', '/var/log/nginx/error.log']
        }

    def _tail(self, path: str, max_lines: int) -> List[str]:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.readlines()[-max_lines:]
        except Exception:
            return []

    def _find_log_files(self, category: str) -> List[str]:
        """Belirli bir kategori için mevcut log dosyalarını bulur"""
        found_files = []
        if category in self.common_log_paths:
            for path in self.common_log_paths[category]:
                if os.path.exists(path) and os.access(path, os.R_OK):
                    found_files.append(path)
        return found_files

    def _read_system_logs(self) -> Dict[str, List[str]]:
        """Read system logs"""
        logs = {}
        
        # System logs
        system_files = self._find_log_files('system')
        if system_files:
            for file_path in system_files:
                content = self._tail(file_path, self.lines)
                logs.setdefault('system', []).extend([line.strip() for line in content])
        
        # Kernel logs
        kernel_files = self._find_log_files('kernel')
        if kernel_files:
            for file_path in kernel_files:
                content = self._tail(file_path, self.lines)
                logs.setdefault('kernel', []).extend([line.strip() for line in content])
        
        # Auth logs
        auth_files = self._find_log_files('auth')
        if auth_files:
            for file_path in auth_files:
                content = self._tail(file_path, self.lines)
                logs.setdefault('auth', []).extend([line.strip() for line in content])
        
        # Daemon logs
        daemon_files = self._find_log_files('daemon')
        if daemon_files:
            for file_path in daemon_files:
                content = self._tail(file_path, self.lines)
                logs.setdefault('daemon', []).extend([line.strip() for line in content])
        
        # Boot logs
        boot_files = self._find_log_files('boot')
        if boot_files:
            for file_path in boot_files:
                content = self._tail(file_path, self.lines)
                logs.setdefault('boot', []).extend([line.strip() for line in content])
        
        # Cron logs
        cron_files = self._find_log_files('cron')
        if cron_files:
            for file_path in cron_files:
                content = self._tail(file_path, self.lines)
                logs.setdefault('cron', []).extend([line.strip() for line in content])
        
        return logs

    def _read_fallback_dir(self) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {}
        if not self.fallback_dir or not os.path.isdir(self.fallback_dir):
            return result
        for name in sorted(os.listdir(self.fallback_dir))[-10:]:
            path = os.path.join(self.fallback_dir, name)
            if os.path.isfile(path) and name.endswith('.log'):
                result.setdefault('system', []).extend([line.strip() for line in self._tail(path, self.lines)])
        return result

    def read_logs(self) -> Dict[str, List[str]]:
        logs: Dict[str, List[str]] = {}
        
        # First read system logs
        system_logs = self._read_system_logs()
        logs.update(system_logs)
        
        # If no logs found, check fallback directory
        if not logs:
            logs = self._read_fallback_dir()
        
        # Also read from manual file_map
        for key, path in self.file_map.items():
            if os.path.exists(path) and os.access(path, os.R_OK):
                content = self._tail(path, self.lines)
                logs.setdefault(key, []).extend([line.strip() for line in content])
        
        return logs


class JournalctlReader(LogReader):
    def __init__(self, priority: Optional[str] = None, lines: int = 1000, output_json: bool = False):
        self.priority = priority
        self.lines = lines
        self.output_json = output_json

    def read_logs(self) -> Dict[str, List[str]]:
        logs = {}
        try:
            # General system logs
            cmd = ["journalctl", "-n", str(self.lines), "--no-pager"]
            if self.priority:
                cmd = ["journalctl", "-p", self.priority, "--no-pager", "-n", str(self.lines)]
            if self.output_json:
                cmd += ["-o", "json"]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                if self.output_json:
                    out: List[str] = []
                    for line in result.stdout.splitlines():
                        try:
                            entry = json.loads(line)
                            out.append(entry.get('MESSAGE', ''))
                        except json.JSONDecodeError:
                            continue
                    logs['system'] = out
                else:
                    logs['system'] = result.stdout.splitlines()
            
            # Kernel logları
            try:
                kernel_cmd = ["journalctl", "-k", "-n", str(self.lines), "--no-pager"]
                kernel_result = subprocess.run(kernel_cmd, capture_output=True, text=True)
                if kernel_result.returncode == 0:
                    logs['kernel'] = kernel_result.stdout.splitlines()
            except Exception:
                pass
            
            # Cron logları
            try:
                cron_cmd = ["journalctl", "_SYSTEMD_UNIT=cron.service", "-n", str(self.lines), "--no-pager"]
                cron_result = subprocess.run(cron_cmd, capture_output=True, text=True)
                if cron_result.returncode == 0:
                    logs['cron'] = cron_result.stdout.splitlines()
            except Exception:
                pass
            
            # Boot logları
            try:
                boot_cmd = ["journalctl", "-b", "-n", str(self.lines), "--no-pager"]
                boot_result = subprocess.run(boot_cmd, capture_output=True, text=True)
                if boot_result.returncode == 0:
                    logs['boot'] = boot_result.stdout.splitlines()
            except Exception:
                pass
            
            # Auth logları
            try:
                auth_cmd = ["journalctl", "_SYSTEMD_UNIT=sshd.service", "-n", str(self.lines), "--no-pager"]
                auth_result = subprocess.run(auth_cmd, capture_output=True, text=True)
                if auth_result.returncode == 0:
                    logs['auth'] = auth_result.stdout.splitlines()
            except Exception:
                pass
            
            return logs
        except Exception:
            return {}


def iter_critical(logs: Iterable[str]) -> Iterable[str]:
    critical_terms = ('ERROR', 'CRITICAL', 'EMERGENCY', 'ALERT', 'FATAL')
    for line in logs:
        try:
            upper = line.upper()
            if any(t in upper for t in critical_terms):
                yield line
        except Exception:
            continue


