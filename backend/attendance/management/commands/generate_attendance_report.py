from datetime import date, timedelta

from django.core.management import BaseCommand

from ...services import AttendanceReportService


class Command(BaseCommand):
    help = 'Generate weekly attendance report (Monday-Sunday) and recalculate hours.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--week-start',
            help='ISO date for week Monday. Defaults to current week.',
        )
        parser.add_argument(
            '--tolerance',
            type=int,
            default=30,
            help='Tolerance in minutes for deviations (default 30).',
        )

    def handle(self, *args, **options):
        if options['week_start']:
            week_start = date.fromisoformat(options['week_start'])
        else:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
        report = AttendanceReportService(week_start, tolerance_minutes=options['tolerance']).generate()
        self.stdout.write(
            self.style.SUCCESS(
                f'Attendance report {report.week_start} - {report.week_end} generated with {report.lines.count()} rows.'
            )
        )


