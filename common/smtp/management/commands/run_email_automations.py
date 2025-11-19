"""
Management command to run scheduled email automations
Run this command periodically (via cron or scheduler) to execute email automations
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from common.smtp.models import EmailAutomation
from common.smtp.automations.cve_email import CVEEmailAutomation
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
        
        if automation_id:
            automations = EmailAutomation.objects.filter(pk=automation_id, is_enabled=True)
        else:
            automations = EmailAutomation.objects.filter(is_enabled=True)
        
        if not automations.exists():
            self.stdout.write(self.style.WARNING('No enabled automations found'))
            return
        
        for automation in automations:
            if not force and not self._should_run(automation):
                continue
            
            self.stdout.write(f'Running automation: {automation.name} (ID: {automation.id})')
            
            try:
                if automation.automation_type == 'cve':
                    handler = CVEEmailAutomation(automation)
                    result = handler.run()
                    
                    if result['success']:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Success: {result['message']} "
                                f"(CVEs: {result['cves_found']}, Emails: {result['emails_sent']})"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"✗ Failed: {result['message']}")
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Automation type "{automation.automation_type}" not yet implemented'
                        )
                    )
                    
            except Exception as e:
                logger.error(f"Error running automation {automation.id}: {e}", exc_info=True)
                self.stdout.write(
                    self.style.ERROR(f'Error: {str(e)}')
                )
    
    def _should_run(self, automation):
        """Check if automation should run based on schedule"""
        now = timezone.now()
        
        if automation.schedule_type == 'daily':
            # Check if it's time to run (within 5 minutes of scheduled time)
            schedule_time = automation.schedule_time
            if schedule_time:
                scheduled_datetime = datetime.combine(now.date(), schedule_time)
                scheduled_datetime = timezone.make_aware(scheduled_datetime)
                
                # Check if we're within 5 minutes of scheduled time
                time_diff = abs((now - scheduled_datetime).total_seconds())
                if time_diff <= 300:  # 5 minutes
                    # Check if we haven't run today
                    if automation.last_run_at:
                        last_run_date = automation.last_run_at.date()
                        if last_run_date == now.date():
                            return False  # Already ran today
                    return True
        
        elif automation.schedule_type == 'weekly':
            # Check if it's the right day and time
            schedule_time = automation.schedule_time
            schedule_days = automation.schedule_days or ''
            
            if schedule_time and schedule_days:
                # Check if today is in schedule_days (0=Monday, 6=Sunday)
                today_weekday = now.weekday()  # 0=Monday, 6=Sunday
                if str(today_weekday) in schedule_days.split(','):
                    scheduled_datetime = datetime.combine(now.date(), schedule_time)
                    scheduled_datetime = timezone.make_aware(scheduled_datetime)
                    
                    time_diff = abs((now - scheduled_datetime).total_seconds())
                    if time_diff <= 300:  # 5 minutes
                        # Check if we haven't run this week
                        if automation.last_run_at:
                            last_run_date = automation.last_run_at.date()
                            week_start = now.date() - timedelta(days=now.weekday())
                            if last_run_date >= week_start:
                                return False  # Already ran this week
                        return True
        
        elif automation.schedule_type == 'custom':
            # For custom cron, we'd need a cron parser
            # For now, just check if it's been a while since last run
            if automation.schedule_cron:
                # Simple check: if last run was more than 23 hours ago
                if automation.last_run_at:
                    time_since_last = (now - automation.last_run_at).total_seconds()
                    if time_since_last < 82800:  # 23 hours
                        return False
                return True
        
        # For monthly or other types, implement as needed
        return False

