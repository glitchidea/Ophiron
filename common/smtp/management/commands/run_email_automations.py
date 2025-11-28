"""
Management command to run scheduled email automations
Run this command periodically (via cron or scheduler) to execute email automations
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from common.smtp.models import EmailAutomation
from common.smtp.services import automation_runner
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run scheduled email automations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--automation-id',
            type=int,
            help='Run specific automation by ID',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force run even if not scheduled',
        )

    def handle(self, *args, **options):
        automation_id = options.get('automation_id')
        force = options.get('force', False)
        
        target_ids = [automation_id] if automation_id else None
        due_ids = automation_runner.collect_due_automation_ids(
            force=force,
            automation_ids=target_ids,
            reference=timezone.now(),
        )

        if not due_ids and not force:
            self.stdout.write(self.style.WARNING('No automations are scheduled to run right now.'))
            return

        if not due_ids and force and target_ids:
            due_ids = target_ids  # Force-run even if scheduling failed

        for automation_id in due_ids:
            automation = EmailAutomation.objects.filter(pk=automation_id).first()
            if not automation:
                continue

            self.stdout.write(f'Running automation: {automation.name} (ID: {automation.id})')

            try:
                result = automation_runner.run_automation_sync(automation_id, force=True)

                if result['success']:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Success: {result['message']} "
                            f"(CVEs: {result.get('cves_found', 0)}, Emails: {result.get('emails_sent', 0)})"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"✗ Failed: {result.get('message', 'Unknown error')}")
                    )
            except Exception as e:
                logger.error(f"Error running automation {automation_id}: {e}", exc_info=True)
                self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))

