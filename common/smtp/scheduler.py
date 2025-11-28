"""
Automation scheduling utilities for SMTP tasks.
Converts user-configured schedules into timezone-aware datetimes.
"""
from __future__ import annotations

import calendar
import logging
from datetime import datetime, timedelta, time, timezone as dt_timezone
from typing import Iterable, Optional

from django.conf import settings
from django.utils import timezone
from zoneinfo import ZoneInfo

try:
    from croniter import croniter
except Exception:  # pragma: no cover - croniter should be installed via requirements
    croniter = None

logger = logging.getLogger(__name__)

DEFAULT_TIME = time(6, 0)
DEFAULT_TZ = getattr(settings, 'TIME_ZONE', 'UTC')


def _get_zone(tz_name: Optional[str]) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name or DEFAULT_TZ)
    except Exception:
        logger.warning("Invalid timezone %s, falling back to %s", tz_name, DEFAULT_TZ)
        return ZoneInfo(DEFAULT_TZ)


def _ensure_time(value: Optional[time]) -> time:
    return value or DEFAULT_TIME


def _parse_days(days_str: Optional[str], default: Iterable[int]) -> Iterable[int]:
    if not days_str:
        return list(default)
    parsed = []
    for token in days_str.split(','):
        token = token.strip()
        if token.isdigit():
            parsed.append(int(token))
    return parsed or list(default)


def _as_local(reference: Optional[datetime], zone: ZoneInfo) -> datetime:
    reference = reference or timezone.now()
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=dt_timezone.utc)
    return reference.astimezone(zone)


def _next_daily(local_now: datetime, schedule_time: time) -> datetime:
    candidate = local_now.replace(
        hour=schedule_time.hour,
        minute=schedule_time.minute,
        second=0,
        microsecond=0,
    )
    if candidate <= local_now:
        candidate += timedelta(days=1)
    return candidate


def _next_weekly(local_now: datetime, schedule_time: time, schedule_days: Iterable[int]) -> datetime:
    schedule_days = sorted({d % 7 for d in schedule_days}) or list(range(7))
    for offset in range(0, 8):
        candidate_day = (local_now.weekday() + offset) % 7
        if candidate_day in schedule_days:
            candidate_date = (local_now + timedelta(days=offset)).date()
            candidate = datetime.combine(candidate_date, schedule_time, tzinfo=local_now.tzinfo)
            if candidate > local_now:
                return candidate
    # Fallback: add a week
    return local_now + timedelta(days=7)


def _next_monthly(local_now: datetime, schedule_time: time, schedule_days: Optional[str]) -> datetime:
    day = 1
    if schedule_days:
        try:
            day = max(1, min(28, int(schedule_days.split(',')[0])))
        except ValueError:
            pass

    year = local_now.year
    month = local_now.month

    for _ in range(0, 14):  # Look ahead up to ~1 year
        _, last_day = calendar.monthrange(year, month)
        target_day = min(day, last_day)
        candidate_date = datetime(year, month, target_day, schedule_time.hour, schedule_time.minute, tzinfo=local_now.tzinfo)
        if candidate_date > local_now:
            return candidate_date
        # Increment month
        month += 1
        if month > 12:
            month = 1
            year += 1

    return local_now + timedelta(days=30)


def _next_custom(local_now: datetime, cron_expr: str, zone: ZoneInfo) -> Optional[datetime]:
    if not croniter:
        logger.error("croniter dependency missing; cannot evaluate custom cron expressions.")
        return None
    try:
        base = local_now.replace(tzinfo=None)
        itr = croniter(cron_expr, base)
        next_naive = itr.get_next(datetime)
        return next_naive.replace(tzinfo=zone)
    except Exception as exc:
        logger.error("Invalid cron expression %s: %s", cron_expr, exc)
        return None


def calculate_next_run(automation, reference: Optional[datetime] = None) -> Optional[datetime]:
    """
    Calculate the next run datetime (UTC) for the given automation.
    Returns None if schedule is invalid.
    """
    tz = _get_zone(getattr(automation, 'timezone', None))
    local_now = _as_local(reference, tz)
    schedule_time = _ensure_time(getattr(automation, 'schedule_time', None))
    schedule_type = getattr(automation, 'schedule_type', 'daily') or 'daily'

    if schedule_type == 'daily':
        next_local = _next_daily(local_now, schedule_time)
    elif schedule_type == 'weekly':
        days = _parse_days(getattr(automation, 'schedule_days', None), default=range(7))
        next_local = _next_weekly(local_now, schedule_time, days)
    elif schedule_type == 'monthly':
        next_local = _next_monthly(local_now, schedule_time, getattr(automation, 'schedule_days', None))
    elif schedule_type == 'custom' and getattr(automation, 'schedule_cron', None):
        next_local = _next_custom(local_now, automation.schedule_cron, tz)
        if next_local and next_local <= local_now:
            # croniter can return current time, ensure strictly future
            next_local = _next_custom(local_now + timedelta(seconds=1), automation.schedule_cron, tz)
    else:
        next_local = None

    if not next_local:
        return None

    return next_local.astimezone(dt_timezone.utc)

