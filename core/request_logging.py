import os
import time
import json
import logging
from datetime import datetime
from typing import Optional

from django.conf import settings
from django.http import HttpRequest, HttpResponse


LOG_DIR = os.path.join(settings.BASE_DIR, 'logger', 'request-access')
os.makedirs(LOG_DIR, exist_ok=True)


def get_client_ip(request: HttpRequest) -> str:
    """
    Get client IP address from request.
    Returns 'unknown' if IP cannot be determined (instead of '0.0.0.0' for security).
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Use first IP in X-Forwarded-For
        return x_forwarded_for.split(',')[0].strip()
    # Use REMOTE_ADDR if available, otherwise return 'unknown' (not '0.0.0.0' for security)
    return request.META.get('REMOTE_ADDR', 'unknown')


def should_skip_logging(request: HttpRequest, response: Optional[HttpResponse]) -> bool:
    path = request.path
    # Skip static/media and health checks
    if path.startswith('/static/') or path.startswith('/media/'):
        return True
    if path in ('/health', '/healthz', '/ready', '/readiness'):
        return True
    # Optionally skip admin static assets
    if path.startswith('/admin/js/') or path.startswith('/admin/css/') or path.startswith('/admin/img/'):
        return True
    return False


class RequestLoggingMiddleware:
    """Middleware to log incoming HTTP requests and responses to daily files.

    Writes JSON lines to logger/request-access/access_YYYY-MM-DD.log
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('ophiron_request_access')
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            # Base stream handler (optional, mostly for console during dev)
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.WARNING)
            self.logger.addHandler(stream_handler)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start_ns = time.perf_counter_ns()

        response = self.get_response(request)

        if should_skip_logging(request, response):
            return response

        try:
            duration_ms = (time.perf_counter_ns() - start_ns) / 1_000_000.0
            now = datetime.now()

            user = getattr(request, 'user', None)
            username = None
            if user is not None and getattr(user, 'is_authenticated', False):
                username = getattr(user, 'username', None)

            record = {
                'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
                'ip': get_client_ip(request),
                'method': request.method,
                'path': request.get_full_path(),
                'status': getattr(response, 'status_code', None),
                'user': username or 'anonymous',
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'referrer': request.META.get('HTTP_REFERER', ''),
                'duration_ms': round(duration_ms, 2),
            }

            log_line = json.dumps(record, ensure_ascii=False)

            # Write to daily file
            daily_file = os.path.join(LOG_DIR, f"access_{now.strftime('%Y-%m-%d')}.log")
            with open(daily_file, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')

        except Exception as e:
            # Avoid breaking requests on logging error
            self.logger.warning(f"request logging failed: {e}")

        return response


