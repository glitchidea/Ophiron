import os
import json
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.http import HttpResponse
from django.http import FileResponse
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.translation import gettext as _
from datetime import datetime, timedelta
from .services.log_analyzer import safe_parse_timestamp
import logging

from .services.log_reader import FileLogReader, JournalctlReader
from .services.log_analyzer import LogAnalyzer
from .services.log_filter import LogFilter
from .services.log_exporter import LogExporter

logger = logging.getLogger(__name__)

def system_logs_page(request):
    context = {
        'page_title': _('System Logs')
    }
    return render(request, 'modules/system_logs/index.html', context)

@require_GET
def list_logs_view(request):
    # Enhanced readers with comprehensive Linux support
    readers = [
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
            lines=500
        ),
        JournalctlReader(lines=500),
    ]

    merged: dict = {}
    for reader in readers:
        data = reader.read_logs()
        for key, values in data.items():
            merged.setdefault(key, []).extend(values)

    # Tüm logları birleştir
    all_logs = []
    for category, logs in merged.items():
        all_logs.extend(logs)

    analyzer = LogAnalyzer()
    analysis = analyzer.analyze_logs(merged or {'system': all_logs})
    
    return JsonResponse({
        'logs': all_logs[-500:],
        'categories': merged,  # Kategorilere göre logları da gönder
        **analysis
    })

@require_GET
def analyze_logs_view(request):
    """Enhanced log analysis endpoint with comprehensive data"""
    try:
        # Enhanced readers with comprehensive Linux support
        readers = [
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
                lines=1000
            ),
            JournalctlReader(lines=1000),
        ]

        merged: dict = {}
        for reader in readers:
            data = reader.read_logs()
            for key, values in data.items():
                merged.setdefault(key, []).extend(values)

        # Tüm logları birleştir
        all_logs = []
        for category, logs in merged.items():
            all_logs.extend(logs)

        # Enhanced analysis
        analyzer = LogAnalyzer()
        analysis = analyzer.analyze_logs(merged or {'system': all_logs})
        
        return JsonResponse(analysis)
        
    except Exception as e:
        logger.error(f"Log analysis error: {str(e)}")
        return JsonResponse({
            'error': str(e),
            'error_count': 0,
            'warning_count': 0,
            'info_count': 0,
            'debug_count': 0,
            'timeline_data': [],
            'common_patterns': {},
            'error_categories': {
                'system': 0,
                'service': 0,
                'permission': 0,
                'network': 0,
                'database': 0,
                'security': 0,
                'other': 0
            },
            'service_stats': {},
            'hourly_distribution': [0] * 24
        })

@require_GET
def detailed_analysis_view(request):
    """Detaylı log analizi endpoint'i - kategorilere ayrılmış detaylı veriler"""
    try:
        # Enhanced readers with comprehensive Linux support
        readers = [
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
                lines=1000
            ),
            JournalctlReader(lines=1000),
        ]

        merged: dict = {}
        for reader in readers:
            data = reader.read_logs()
            for key, values in data.items():
                merged.setdefault(key, []).extend(values)

        # Detaylı analiz
        analyzer = LogAnalyzer()
        detailed_analysis = analyzer.analyze_logs_detailed(merged or {'system': []})
        
        return JsonResponse(detailed_analysis)
        
    except Exception as e:
        logger.error(f"Detailed log analysis error: {str(e)}")
        return JsonResponse({
            'error': str(e),
            'errors': [],
            'warnings': [],
            'security': [],
            'debug': [],
            'services': [],
            'error_categories': {},
            'warning_stats': {},
            'security_categories': {},
            'debug_stats': {},
            'service_stats': {}
        })


@require_GET
def export_logs_view(request):
    format_ = request.GET.get('format', 'csv').lower()
    level = request.GET.get('level', 'all')
    categories = request.GET.get('categories', '').split(',') if request.GET.get('categories') else []
    
    try:
        # Define available log sources
        log_sources = {
            'system': '/var/log/syslog',
            'kernel': '/var/log/kern.log',
            'auth': '/var/log/auth.log',
            'daemon': '/var/log/daemon.log',
            'boot': '/var/log/boot.log',
            'cron': '/var/log/cron.log',
        }
        
        # Filter sources based on selected categories
        if categories and 'all' not in categories:
            filtered_sources = {k: v for k, v in log_sources.items() if k in categories}
        else:
            filtered_sources = log_sources
        
        # Get logs data from selected sources only
        readers = [
            FileLogReader(
                file_map=filtered_sources, 
                fallback_dir=os.path.join(settings.BASE_DIR, 'logger', 'error-login'), 
                lines=1000
            ),
        ]
        
        # Only add JournalctlReader if system logs are requested
        if not categories or 'system' in categories or 'all' in categories:
            readers.append(JournalctlReader(lines=1000))

        merged: dict = {}
        for reader in readers:
            data = reader.read_logs()
            for key, values in data.items():
                # Only include categories that were selected
                if not categories or 'all' in categories or key in categories:
                    merged.setdefault(key, []).extend(values)

        # Export logs
        exporter = LogExporter()
        if format_ == 'csv':
            return exporter.export_to_csv(merged, level)
        elif format_ == 'json':
            return exporter.export_to_json(merged, level)
        elif format_ == 'syslog':
            return exporter.export_to_syslog(merged, level)
        else:
            return JsonResponse({'error': 'Unsupported format'}, status=400)
            
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def filter_logs_view(request):
    level = request.GET.get('level', 'all')
    search = request.GET.get('search', '')
    
    try:
        # Get logs data
        readers = [
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
                lines=500
            ),
            JournalctlReader(lines=500),
        ]

        merged: dict = {}
        for reader in readers:
            data = reader.read_logs()
            for key, values in data.items():
                merged.setdefault(key, []).extend(values)

        # Filter logs
        filter_service = LogFilter()
        filtered_logs = filter_service.filter_logs(merged, level, search)
        
        return JsonResponse({
            'logs': filtered_logs,
            'count': len(filtered_logs)
        })
        
    except Exception as e:
        logger.error(f"Filter error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def critical_logs_view(request):
    try:
        # Get critical logs
        readers = [
            FileLogReader(
                file_map={
                    'system': '/var/log/syslog',
                    'kernel': '/var/log/kern.log',
                    'auth': '/var/log/auth.log',
                }, 
                fallback_dir=os.path.join(settings.BASE_DIR, 'logger', 'error-login'), 
                lines=500
            ),
            JournalctlReader(lines=500),
        ]

        merged: dict = {}
        for reader in readers:
            data = reader.read_logs()
            for key, values in data.items():
                merged.setdefault(key, []).extend(values)

        # Filter critical logs
        critical_logs = []
        for category, logs in merged.items():
            for log in logs:
                if any(keyword in log.lower() for keyword in ['error', 'critical', 'fatal', 'emergency']):
                    critical_logs.append(log)
        
        return JsonResponse({
            'logs': critical_logs[-100:],  # Last 100 critical logs
            'count': len(critical_logs)
        })
        
    except Exception as e:
        logger.error(f"Critical logs error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def recent_logs_summary_view(request):
    try:
        # Get recent logs summary
        readers = [
            FileLogReader(
                file_map={
                    'system': '/var/log/syslog',
                    'kernel': '/var/log/kern.log',
                    'auth': '/var/log/auth.log',
                }, 
                fallback_dir=os.path.join(settings.BASE_DIR, 'logger', 'error-login'), 
                lines=100
            ),
            JournalctlReader(lines=100),
        ]

        merged: dict = {}
        for reader in readers:
            data = reader.read_logs()
            for key, values in data.items():
                merged.setdefault(key, []).extend(values)

        # Analyze recent logs
        analyzer = LogAnalyzer()
        analysis = analyzer.analyze_logs(merged)
        
        return JsonResponse(analysis)
        
    except Exception as e:
        logger.error(f"Recent logs summary error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def logs_by_level_view(request, level):
    try:
        # Get logs by level
        readers = [
            FileLogReader(
                file_map={
                    'system': '/var/log/syslog',
                    'kernel': '/var/log/kern.log',
                    'auth': '/var/log/auth.log',
                }, 
                fallback_dir=os.path.join(settings.BASE_DIR, 'logger', 'error-login'), 
                lines=500
            ),
            JournalctlReader(lines=500),
        ]

        merged: dict = {}
        for reader in readers:
            data = reader.read_logs()
            for key, values in data.items():
                merged.setdefault(key, []).extend(values)

        # Filter by level
        filter_service = LogFilter()
        filtered_logs = filter_service.filter_logs(merged, level)
        
        return JsonResponse({
            'logs': filtered_logs,
            'level': level,
            'count': len(filtered_logs)
        })
        
    except Exception as e:
        logger.error(f"Logs by level error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# Own logs views (application logs)
def own_logs_page(request):
    context = {
        'page_title': _('Application Logs')
    }
    return render(request, 'modules/system_logs/own_logs.html', context)


@require_GET
def own_logs_api(request):
    return JsonResponse({'message': 'Own logs API'})


# Additional own logs views
@require_GET
def own_categories_view(request):
    """Get available log categories from logger directory"""
    try:
        logger_dir = os.path.join(settings.BASE_DIR, 'logger')
        if not os.path.exists(logger_dir):
            return JsonResponse({'categories': []})
        
        categories = []
        for item in os.listdir(logger_dir):
            item_path = os.path.join(logger_dir, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                # Check if directory has log files
                log_files = [f for f in os.listdir(item_path) if f.endswith('.log')]
                if log_files:
                    categories.append(item)
        
        return JsonResponse({'categories': sorted(categories)})
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        return JsonResponse({'categories': []})


@require_GET
def own_category_files_view(request, category):
    """Get log files for a specific category"""
    try:
        logger_dir = os.path.join(settings.BASE_DIR, 'logger', category)
        if not os.path.exists(logger_dir):
            return JsonResponse({'files': []})
        
        log_files = []
        for filename in os.listdir(logger_dir):
            if filename.endswith('.log'):
                file_path = os.path.join(logger_dir, filename)
                if os.path.isfile(file_path):
                    # Get file stats
                    stat = os.stat(file_path)
                    log_files.append({
                        'name': filename,
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'size_human': _format_file_size(stat.st_size)
                    })
        
        # Sort by modification time (newest first)
        log_files.sort(key=lambda x: x['modified'], reverse=True)
        return JsonResponse({'files': [f['name'] for f in log_files]})
    except Exception as e:
        logger.error(f"Error getting files for category {category}: {str(e)}")
        return JsonResponse({'files': []})


@require_GET
def own_file_lines_view(request, category, filename):
    """Get log lines from a specific file"""
    try:
        file_path = os.path.join(settings.BASE_DIR, 'logger', category, filename)
        if not os.path.exists(file_path):
            return JsonResponse({'lines': [], 'total': 0, 'page_size': 200})
        
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 200))
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        page_lines = lines[start_idx:end_idx]
        
        return JsonResponse({
            'lines': [line.rstrip('\n\r') for line in page_lines],
            'total': total_lines,
            'page_size': page_size
        })
    except Exception as e:
        logger.error(f"Error reading file {filename} in category {category}: {str(e)}")
        return JsonResponse({'lines': [], 'total': 0, 'page_size': 200})


@require_GET
def own_category_days_view(request, category):
    """Get available days for a category"""
    try:
        logger_dir = os.path.join(settings.BASE_DIR, 'logger', category)
        if not os.path.exists(logger_dir):
            return JsonResponse({'days': []})
        
        days = set()
        for filename in os.listdir(logger_dir):
            if filename.endswith('.log'):
                # Extract date from filename (assuming format: module_YYYY-MM-DD.log)
                parts = filename.split('_')
                if len(parts) >= 2:
                    date_part = parts[-1].replace('.log', '')
                    if len(date_part) == 10 and date_part.count('-') == 2:
                        days.add(date_part)
        
        return JsonResponse({'days': sorted(days, reverse=True)})
    except Exception as e:
        logger.error(f"Error getting days for category {category}: {str(e)}")
        return JsonResponse({'days': []})


@require_GET
def own_download_day_view(request, category, day):
    """Download all logs for a specific day"""
    try:
        logger_dir = os.path.join(settings.BASE_DIR, 'logger', category)
        if not os.path.exists(logger_dir):
            return JsonResponse({'error': 'Category not found'}, status=404)
        
        # Find all files for the day
        day_files = []
        for filename in os.listdir(logger_dir):
            if day in filename and filename.endswith('.log'):
                day_files.append(os.path.join(logger_dir, filename))
        
        if not day_files:
            return JsonResponse({'error': 'No files found for the specified day'}, status=404)
        
        # Combine all files for the day
        combined_content = []
        for file_path in sorted(day_files):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                combined_content.append(f"=== {os.path.basename(file_path)} ===\n")
                combined_content.append(f.read())
                combined_content.append("\n\n")
        
        response = HttpResponse(''.join(combined_content), content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{category}_{day}.log"'
        return response
    except Exception as e:
        logger.error(f"Error downloading day {day} for category {category}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def own_download_all_view(request, category):
    """Download all logs for a category"""
    try:
        logger_dir = os.path.join(settings.BASE_DIR, 'logger', category)
        if not os.path.exists(logger_dir):
            return JsonResponse({'error': 'Category not found'}, status=404)
        
        # Find all log files
        log_files = []
        for filename in os.listdir(logger_dir):
            if filename.endswith('.log'):
                log_files.append(os.path.join(logger_dir, filename))
        
        if not log_files:
            return JsonResponse({'error': 'No log files found'}, status=404)
        
        # Combine all files
        combined_content = []
        for file_path in sorted(log_files):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                combined_content.append(f"=== {os.path.basename(file_path)} ===\n")
                combined_content.append(f.read())
                combined_content.append("\n\n")
        
        response = HttpResponse(''.join(combined_content), content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{category}_all.log"'
        return response
    except Exception as e:
        logger.error(f"Error downloading all logs for category {category}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def own_download_file_view(request, category, filename):
    """Download a specific log file"""
    try:
        file_path = os.path.join(settings.BASE_DIR, 'logger', category, filename)
        if not os.path.exists(file_path):
            return JsonResponse({'error': 'File not found'}, status=404)
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        logger.error(f"Error downloading file {filename} from category {category}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def own_live_config_view(request):
    return JsonResponse({'config': {}})


@require_GET
def own_all_lines_view(request, category):
    """Get all lines from all files in a category, sorted chronologically"""
    try:
        logger_dir = os.path.join(settings.BASE_DIR, 'logger', category)
        logger.info(f"Looking for logs in directory: {logger_dir}")
        
        if not os.path.exists(logger_dir):
            logger.error(f"Logger directory does not exist: {logger_dir}")
            return JsonResponse({'lines': []})
        
        all_log_entries = []
        log_files = [f for f in os.listdir(logger_dir) if f.endswith('.log')]
        logger.info(f"Found {len(log_files)} log files: {log_files}")
        
        # Read all files and collect log entries (simplified approach)
        all_lines = []
        for filename in log_files:
            file_path = os.path.join(logger_dir, filename)
            if not os.path.isfile(file_path):
                logger.warning(f"File is not a regular file: {file_path}")
                continue
                
            try:
                logger.info(f"Reading file: {filename}")
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    logger.info(f"Read {len(lines)} lines from {filename}")
                    
                for line_num, line in enumerate(lines, 1):
                    line = line.rstrip('\n\r')
                    if line.strip():  # Skip empty lines
                        all_lines.append(line)
                        logger.info(f"Added line: {line[:50]}...")
                        
            except Exception as e:
                logger.error(f"Error reading file {filename}: {str(e)}")
                continue
        
        logger.info(f"Total lines collected: {len(all_lines)}")
        logger.info(f"Returning {len(all_lines)} lines to frontend")
        
        return JsonResponse({'lines': all_lines})
    except Exception as e:
        logger.error(f"Error getting all lines for category {category}: {str(e)}")
        return JsonResponse({'lines': []})


@require_GET
def own_day_lines_view(request, category, day):
    """Get all lines from files for a specific day"""
    try:
        logger_dir = os.path.join(settings.BASE_DIR, 'logger', category)
        if not os.path.exists(logger_dir):
            return JsonResponse({'lines': []})
        
        all_lines = []
        day_files = []
        
        # Find files for the specific day
        for filename in os.listdir(logger_dir):
            if day in filename and filename.endswith('.log'):
                day_files.append(filename)
        
        if not day_files:
            return JsonResponse({'lines': []})
        
        # Sort files by modification time
        day_files_with_time = []
        for filename in day_files:
            file_path = os.path.join(logger_dir, filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                day_files_with_time.append((filename, stat.st_mtime))
        
        day_files_with_time.sort(key=lambda x: x[1], reverse=True)
        
        for filename, _ in day_files_with_time:
            file_path = os.path.join(logger_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    # Add file header
                    all_lines.append(f"=== {filename} ===")
                    all_lines.extend([line.rstrip('\n\r') for line in lines])
                    all_lines.append("")  # Empty line between files
            except Exception as e:
                logger.error(f"Error reading file {filename}: {str(e)}")
                continue
        
        return JsonResponse({'lines': all_lines})
    except Exception as e:
        logger.error(f"Error getting day lines for category {category}, day {day}: {str(e)}")
        return JsonResponse({'lines': []})


def _format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def _extract_timestamp_from_log(log_line):
    """Extract timestamp from log line for chronological sorting"""
    import re
    from datetime import datetime
    
    # Common timestamp patterns
    timestamp_patterns = [
        # ISO format: 2024-01-15T10:30:45.123456
        r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?)',
        # Standard format: 2024-01-15 10:30:45
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
        # Short format: Jan 15 10:30:45
        r'(\w{3} \d{1,2} \d{2}:\d{2}:\d{2})',
        # Time only: 10:30:45
        r'(\d{2}:\d{2}:\d{2})',
        # Django format: [15/Jan/2024 10:30:45]
        r'\[(\d{1,2}/\w{3}/\d{4} \d{2}:\d{2}:\d{2})\]',
        # Custom format: 2024-01-15 10:30:45,123
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})'
    ]
    
    for pattern in timestamp_patterns:
        match = re.search(pattern, log_line)
        if match:
            timestamp_str = match.group(1)
            try:
                # Try different datetime formats
                formats = [
                    '%Y-%m-%dT%H:%M:%S.%f',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%d %H:%M:%S',
                    '%b %d %H:%M:%S',
                    '%H:%M:%S',
                    '%d/%b/%Y %H:%M:%S',
                    '%Y-%m-%d %H:%M:%S,%f'
                ]
                
                for fmt in formats:
                    try:
                        if fmt == '%H:%M:%S':
                            # For time-only, use today's date
                            from datetime import date
                            today = date.today()
                            full_timestamp = f"{today} {timestamp_str}"
                            return safe_parse_timestamp(full_timestamp).timestamp()
                        else:
                            return safe_parse_timestamp(timestamp_str).timestamp()
                    except ValueError:
                        continue
            except (ValueError, TypeError):
                continue
    
    # If no timestamp found, use current time (will be sorted to end)
    logger.warning(f"No timestamp found in log line: {log_line[:100]}...")
    return datetime.now().timestamp()


@require_GET
def own_config_get_view(request):
    from .models import SystemLogsSettings
    settings = SystemLogsSettings.get_global_settings()
    return JsonResponse({
        'config': {
            'enabled': settings.live_mode_enabled,
            'interval_sec': settings.monitoring_interval,
            'logging_enabled': settings.logging_enabled,
            'realtime_logging': settings.realtime_logging
        }
    })


@require_POST
def own_config_update_view(request):
    try:
        import json
        from .models import SystemLogsSettings
        
        data = json.loads(request.body)
        enabled = data.get('enabled', False)
        interval_sec = data.get('interval_sec', 5)
        
        # Get or create settings instance
        settings = SystemLogsSettings.get_global_settings()
        
        # Update settings
        settings.live_mode_enabled = enabled
        settings.monitoring_interval = float(interval_sec)
        settings.last_modified_by = request.user.username if request.user.is_authenticated else 'anonymous'
        settings.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Application Logs live mode {"enabled" if enabled else "disabled"}',
            'config': {
                'enabled': settings.live_mode_enabled,
                'interval_sec': settings.monitoring_interval,
                'logging_enabled': settings.logging_enabled,
                'realtime_logging': settings.realtime_logging
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_GET
def own_all_lines_view(request, category):
    """Get all lines from all files in a category, sorted chronologically"""
    try:
        logger_dir = os.path.join(settings.BASE_DIR, 'logger', category)
        if not os.path.exists(logger_dir):
            return JsonResponse({'lines': []})
        log_files = [f for f in os.listdir(logger_dir) if f.endswith('.log')]
        all_lines = []
        for filename in log_files:
            file_path = os.path.join(logger_dir, filename)
            if not os.path.isfile(file_path):
                continue
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                for line in lines:
                    line = line.rstrip('\n\r')
                    if line.strip():
                        all_lines.append(line)
            except Exception:
                continue
        return JsonResponse({'lines': all_lines})
    except Exception:
        return JsonResponse({'lines': []})


@require_GET
def own_day_lines_view(request, category, day):
    """Get all lines from files for a specific day"""
    try:
        logger_dir = os.path.join(settings.BASE_DIR, 'logger', category)
        if not os.path.exists(logger_dir):
            return JsonResponse({'lines': []})
        all_lines = []
        for filename in os.listdir(logger_dir):
            if day in filename and filename.endswith('.log'):
                file_path = os.path.join(logger_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    all_lines.append(f"=== {filename} ===")
                    all_lines.extend([line.rstrip('\n\r') for line in lines])
                    all_lines.append("")
                except Exception:
                    continue
        return JsonResponse({'lines': all_lines})
    except Exception:
        return JsonResponse({'lines': []})