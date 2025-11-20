from django.core.management import BaseCommand

from ...services import WorkSessionService


class Command(BaseCommand):
    help = 'Closes work sessions that were not explicitly finished before midnight.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--grace-minutes',
            type=int,
            default=5,
            help='Minutes to wait after midnight before auto-closing the session (default: 5).',
        )

    def handle(self, *args, **options):
        grace = options['grace_minutes']
        closed = WorkSessionService.close_overdue_sessions(cutoff_minutes=grace)
        self.stdout.write(self.style.SUCCESS(f'Auto-closed {closed} overdue sessions.'))


