"""
Reusable helpers for scheduling and executing SMTP automations.
Provides a single place that Celery tasks, management commands and views can call.
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Dict, List, Optional

from django.db import transaction
from django.utils import timezone

from common.smtp.automations.cve_email import CVEEmailAutomation
from common.smtp.models import EmailAutomation

logger = logging.getLogger(__name__)

HANDLER_MAP = {
    'cve': CVEEmailAutomation,
}


def _get_handler(automation: EmailAutomation):
    handler_cls = HANDLER_MAP.get(automation.automation_type)
    if not handler_cls:
        return None
    return handler_cls(automation)


def run_automation_sync(automation_id: int, force: bool = False) -> Dict:
    """Run an automation immediately in the current process."""
    try:
        automation = EmailAutomation.objects.get(pk=automation_id)
    except EmailAutomation.DoesNotExist:
        return {
            'success': False,
            'message': 'Automation not found',
            'cves_found': 0,
            'emails_sent': 0,
        }

    if not force and not automation.is_enabled:
        return {
            'success': False,
            'message': 'Automation disabled',
            'cves_found': 0,
            'emails_sent': 0,
        }

    handler = _get_handler(automation)
    if not handler:
        msg = f'No handler registered for automation type "{automation.automation_type}"'
        logger.warning(msg)
        return {
            'success': False,
            'message': msg,
            'cves_found': 0,
            'emails_sent': 0,
        }

    result = handler.run()
    automation.update_next_run()
    return result


def collect_due_automation_ids(
    force: bool = False,
    automation_ids: Optional[List[int]] = None,
    reference: Optional[timezone.datetime] = None,
) -> List[int]:
    """
    Determine which automations should run now.
    Ensures next_run_at is advanced so each automation is queued at most once per slot.
    """
    reference = reference or timezone.now()
    qs = EmailAutomation.objects.all()
    if automation_ids:
        qs = qs.filter(pk__in=automation_ids)
    elif not force:
        qs = qs.filter(is_enabled=True)

    ids = list(qs.values_list('id', flat=True))
    due_ids: List[int] = []

    for automation_id in ids:
        with transaction.atomic():
            locked = (
                EmailAutomation.objects.select_for_update(skip_locked=True)
                .filter(pk=automation_id)
                .first()
            )
            if not locked:
                continue

            if not force and not locked.is_enabled:
                continue

            due_time = locked.next_run_at
            if not due_time:
                due_time = locked.update_next_run(reference=reference, commit=True)

            if due_time is None:
                logger.warning(
                    "Automation %s has invalid schedule; skipping until configuration is fixed.",
                    locked.id,
                )
                continue

            should_run = force or (due_time and due_time <= reference)

            if should_run:
                # Advance to the next slot to avoid double scheduling
                next_reference = (due_time or reference) + timedelta(seconds=1)
                locked.update_next_run(reference=next_reference, commit=True)
                due_ids.append(locked.id)

    return due_ids

