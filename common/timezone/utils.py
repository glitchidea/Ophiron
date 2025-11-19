"""
Timezone utility helpers used across the project.
Keep all timezone selection, validation and formatting logic here
to avoid bloating views with repeated code.
"""

from __future__ import annotations

from typing import Optional, List
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones


SESSION_KEY = 'user_timezone'


def resolve_zoneinfo(tz_name: Optional[str]) -> Optional[ZoneInfo]:
    """Safely resolve a timezone name to ZoneInfo or return None if invalid."""
    if not tz_name:
        return None
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return None


def get_user_timezone(request) -> Optional[ZoneInfo]:
    """Get user's timezone from session, as ZoneInfo or None."""
    tz_name = request.session.get(SESSION_KEY)
    return resolve_zoneinfo(tz_name)


def set_user_timezone(request, tz_name: str) -> bool:
    """
    Validate and persist timezone name in session.
    Returns True if saved, False if invalid.
    """
    tz = resolve_zoneinfo(tz_name)
    if tz is None:
        return False
    request.session[SESSION_KEY] = tz_name
    return True


def to_local(dt: datetime, tz: Optional[ZoneInfo]) -> datetime:
    """Convert aware datetime to the user's timezone if provided."""
    if not isinstance(dt, datetime):
        return dt
    if tz is None:
        return dt
    try:
        return dt.astimezone(tz)
    except Exception:
        return dt


def format_dt(dt: datetime, tz: Optional[ZoneInfo], fmt: str) -> str:
    """Format datetime with optional timezone conversion using provided format."""
    return to_local(dt, tz).strftime(fmt)


def list_timezones() -> List[str]:
    """Return a sorted list of all available timezone names (IANA database)."""
    try:
        tz_set = available_timezones()
    except Exception:
        tz_set = set()
    # Prefer common style names containing '/'; always include 'UTC' on top
    tz_list = sorted([tz for tz in tz_set if '/' in tz])
    if 'UTC' in tz_set:
        return ['UTC'] + tz_list
    return tz_list


