import csv
import json
import logging
from datetime import datetime
from django.http import HttpResponse, JsonResponse
import io


class LogExporter:
    def export_to_csv(self, logs, level='all'):
        # Prepare CSV data in memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Timestamp', 'Level', 'Message', 'Source'])
        
        # Flatten logs data
        all_logs = []
        for category, log_list in logs.items():
            for log_entry in log_list:
                if isinstance(log_entry, dict):
                    all_logs.append({
                        'timestamp': log_entry.get('timestamp', ''),
                        'level': log_entry.get('level', 'info'),
                        'message': log_entry.get('message', ''),
                        'source': category
                    })
                else:
                    # Handle string logs
                    all_logs.append({
                        'timestamp': '',
                        'level': 'info',
                        'message': str(log_entry),
                        'source': category
                    })
        
        # Filter by level if specified
        if level != 'all':
            all_logs = [log for log in all_logs if log['level'].lower() == level.lower()]
        
        # Write to CSV
        for log in all_logs:
            writer.writerow([log['timestamp'], log['level'], log['message'], log['source']])
        
        # Create HTTP response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="system_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        response.write(output.getvalue())
        return response

    def export_to_json(self, logs, level='all'):
        # Flatten logs data
        all_logs = []
        for category, log_list in logs.items():
            for log_entry in log_list:
                if isinstance(log_entry, dict):
                    log_entry['source'] = category
                    all_logs.append(log_entry)
                else:
                    # Handle string logs
                    all_logs.append({
                        'timestamp': '',
                        'level': 'info',
                        'message': str(log_entry),
                        'source': category
                    })
        
        # Filter by level if specified
        if level != 'all':
            all_logs = [log for log in all_logs if log.get('level', 'info').lower() == level.lower()]
        
        # Create HTTP response
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="system_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
        response.write(json.dumps(all_logs, indent=2, ensure_ascii=False))
        return response

    def export_to_syslog(self, logs, level='all'):
        # Flatten logs data
        all_logs = []
        for category, log_list in logs.items():
            for log_entry in log_list:
                if isinstance(log_entry, dict):
                    all_logs.append(log_entry)
                else:
                    # Handle string logs
                    all_logs.append({
                        'timestamp': '',
                        'level': 'info',
                        'message': str(log_entry)
                    })
        
        # Filter by level if specified
        if level != 'all':
            all_logs = [log for log in all_logs if log.get('level', 'info').lower() == level.lower()]
        
        # Create syslog format text
        syslog_content = ""
        for log in all_logs:
            timestamp = log.get('timestamp', '')
            level = log.get('level', 'info')
            message = log.get('message', '')
            syslog_content += f"[{timestamp}] [{level.upper()}] {message}\n"
        
        # Create HTTP response
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="system_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log"'
        response.write(syslog_content)
        return response

    def format_for_elk(self, logs):
        elk_logs = []
        for log in logs:
            elk_log = {
                "@timestamp": log.get('timestamp', datetime.now().isoformat()),
                "level": log.get('level', 'info'),
                "message": log.get('message', ''),
                "source": "system_monitor",
                "host": {
                    "name": "system_monitor"
                },
                "log": {
                    "logger": "system_monitor_app"
                },
                "event": {
                    "dataset": "system_monitor.logs"
                }
            }
            elk_logs.append(elk_log)
        return elk_logs


