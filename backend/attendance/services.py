from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.utils import timezone

from staff.models import Employee

from .models import (
    AttendanceReport,
    AttendanceReportLine,
    EmployeeSchedule,
    ScheduleTemplate,
    WorkSession,
)


class WorkSessionService:
    """
    Utility helpers for tracking work sessions.
    """

    @staticmethod
    def close_overdue_sessions(cutoff_minutes: int = 5) -> int:
        """
        Closes sessions that passed midnight without explicit logout.
        """
        now = timezone.now()
        cutoff = now - timedelta(minutes=cutoff_minutes)
        sessions = WorkSession.objects.filter(ended_at__isnull=True, started_at__date__lt=cutoff.date())
        closed = 0
        for session in sessions:
            session_end = timezone.make_aware(
                datetime.combine(session.started_at.date(), time(hour=23, minute=59)),
                timezone=session.started_at.tzinfo,
            )
            session.ended_at = session_end
            session.auto_closed = True
            session.save(update_fields=['ended_at', 'auto_closed'])
            closed += 1
        return closed


class AttendanceReportService:
    """
    Generates weekly attendance reports with tolerance support (default 30 minutes).
    """

    def __init__(self, week_start: date, generated_by: Optional[Employee] = None, tolerance_minutes: int = 30):
        self.week_start = week_start
        self.week_end = week_start + timedelta(days=6)
        self.generated_by = generated_by
        self.tolerance_minutes = tolerance_minutes

    @transaction.atomic
    def generate(self) -> AttendanceReport:
        report, created = AttendanceReport.objects.get_or_create(
            week_start=self.week_start,
            week_end=self.week_end,
            defaults={
                'generated_by': self.generated_by,
                'tolerance_minutes': self.tolerance_minutes,
            },
        )
        if not created:
            report.lines.all().delete()
            report.status = AttendanceReport.DRAFT
            report.generated_by = self.generated_by
            report.tolerance_minutes = self.tolerance_minutes
            report.save(update_fields=['status', 'generated_by', 'tolerance_minutes'])

        employees = Employee.objects.filter(status=Employee.ACTIVE).select_related('position')
        for employee in employees:
            expected = self._expected_hours(employee)
            actual = self._actual_hours(employee)
            delta = actual - expected
            tolerance_hours = Decimal(self.tolerance_minutes) / Decimal(60)
            if abs(delta) < tolerance_hours:
                delta = Decimal('0')
            line = AttendanceReportLine.objects.create(
                report=report,
                employee=employee,
                expected_hours=expected,
                actual_hours=actual,
                delta_hours=delta,
                approved_hours=actual,
            )
            if delta > 0:
                line.note = 'Переработка'
                line.save(update_fields=['note'])
            elif delta < 0:
                line.note = 'Недоработка'
                line.save(update_fields=['note'])
        return report

    def submit(self, report: AttendanceReport) -> AttendanceReport:
        if report.status != AttendanceReport.DRAFT:
            return report
        report.status = AttendanceReport.SUBMITTED
        report.submitted_at = timezone.now()
        report.save(update_fields=['status', 'submitted_at'])
        return report

    def approve(self, report: AttendanceReport, director: Employee, comment: str = '') -> AttendanceReport:
        report.status = AttendanceReport.APPROVED
        report.approved_by = director
        report.approved_at = timezone.now()
        if comment:
            report.comment = comment
        report.save(update_fields=['status', 'approved_by', 'approved_at', 'comment'])
        return report

    def _expected_hours(self, employee: Employee) -> Decimal:
        assignment = getattr(employee, 'schedule_assignment', None)
        if not assignment:
            return Decimal('40.00')
        weekdays = assignment.template.weekdays or {}
        result = Decimal('0')
        tz = timezone.get_current_timezone()
        for day in range(7):
            current_date = self.week_start + timedelta(days=day)
            day_key = current_date.strftime('%a').lower()[:3]
            hours = weekdays.get(day_key)
            if not hours or len(hours) < 2:
                continue
            try:
                start_time = datetime.strptime(hours[0], '%H:%M').time()
                end_time = datetime.strptime(hours[1], '%H:%M').time()
            except ValueError:
                continue
            start_dt = timezone.make_aware(datetime.combine(current_date, start_time), tz)
            end_dt = timezone.make_aware(datetime.combine(current_date, end_time), tz)
            delta = end_dt - start_dt
            result += Decimal(delta.total_seconds()) / Decimal(3600)
        return result.quantize(Decimal('0.01'))

    def _actual_hours(self, employee: Employee) -> Decimal:
        tz = timezone.get_current_timezone()
        range_start = timezone.make_aware(datetime.combine(self.week_start, time.min), tz)
        range_end = timezone.make_aware(datetime.combine(self.week_end, time.max), tz)
        sessions = employee.sessions.filter(started_at__lte=range_end).order_by('started_at')
        total = Decimal('0')
        for session in sessions:
            start = max(session.started_at, range_start)
            end = session.ended_at or timezone.now()
            end = min(end, range_end)
            if end <= start:
                continue
            duration = end - start
            total += Decimal(duration.total_seconds()) / Decimal(3600)
        return total.quantize(Decimal('0.01'))


