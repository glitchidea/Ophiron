import re
from datetime import datetime


class LogFilter:
    def filter_by_level(self, logs, level):
        if level == 'all':
            return logs

        level_patterns = {
            'error': r'(?i)(error|critical|emergency)',
            'warning': r'(?i)(warning|warn)',
            'info': r'(?i)(info|notice)',
            'debug': r'(?i)(debug)'
        }

        pattern = level_patterns.get(level, '')
        if not pattern:
            return logs
        return [log for log in logs if re.search(pattern, str(log))]

    def filter_by_date_range(self, logs, start_date, end_date):
        if not start_date or not end_date:
            return logs

        start = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
        end = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')

        filtered_logs = []
        for log in logs:
            timestamp_match = re.search(r'\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}', str(log))
            if timestamp_match:
                log_date = datetime.strptime(timestamp_match.group(), '%b %d %H:%M:%S')
                if start <= log_date <= end:
                    filtered_logs.append(log)

        return filtered_logs


