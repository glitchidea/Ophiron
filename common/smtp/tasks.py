"""
Celery tasks for SMTP automations.
These are thin wrappers around automation_runner helpers so they can be reused elsewhere.
"""
import logging

from celery import shared_task

from common.smtp.services import automation_runner

logger = logging.getLogger(__name__)


@shared_task(name='smtp.enqueue_due_automations')
def enqueue_due_automations(force: bool = False):
    due_ids = automation_runner.collect_due_automation_ids(force=force)
    for automation_id in due_ids:
        run_automation.delay(automation_id)
    logger.debug("Enqueued %s automation(s) for SMTP processing.", len(due_ids))
    return {'queued': len(due_ids)}


@shared_task(name='smtp.run_automation')
def run_automation(automation_id: int, force: bool = False):
    result = automation_runner.run_automation_sync(automation_id, force=force)
    logger.debug("Automation %s finished with status: %s", automation_id, result.get('message'))
    return result

