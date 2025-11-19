import os
from typing import Dict, List
from django.conf import settings
from .log_reader import FileLogReader, JournalctlReader
from .log_filter import LogFilter


class LogService:
    """Facade service to read and filter logs in a reusable, modular way."""

    def __init__(self, lines: int = 1000):
        self.lines = lines
        self._readers = [
            FileLogReader(
                file_map={
                    'system': '/var/log/syslog',
                    'kernel': '/var/log/kern.log',
                    'auth': '/var/log/auth.log',
                    'daemon': '/var/log/daemon.log',
                    'boot': '/var/log/boot.log',
                    'cron': '/var/log/cron.log',
                },
                fallback_dir=os.path.join(settings.BASE_DIR, 'logger', 'error-login'),
                lines=self.lines,
            ),
            JournalctlReader(lines=self.lines),
        ]
        self._filter = LogFilter()

    def get_combined_logs(self) -> Dict[str, List[str]]:
        merged: Dict[str, List[str]] = {}
        for reader in self._readers:
            data = reader.read_logs()
            for key, values in data.items():
                merged.setdefault(key, []).extend(values)
        return merged

    def get_logs_by_level(self, level: str) -> List[str]:
        """Return a flat list of logs filtered by severity level or all."""
        merged = self.get_combined_logs()
        # Flatten all categories into a single list for level filtering
        flat: List[str] = []
        for values in merged.values():
            flat.extend(values)
        if level == 'all':
            return flat
        return self._filter.filter_by_level(flat, level)


