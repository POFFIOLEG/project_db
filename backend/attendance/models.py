from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models


class ScheduleTemplate(models.Model):
    name = models.CharField(max_length=128, unique=True)
    position = models.ForeignKey('staff.Position', on_delete=models.CASCADE, related_name='schedules')
    weekdays = models.JSONField(default=dict)  # {'mon': ['08:00', '17:00'], ...}

    def __str__(self) -> str:
        return self.name


class WorkSession(models.Model):
    employee = models.ForeignKey('staff.Employee', on_delete=models.CASCADE, related_name='sessions')
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=64, default='system')

    def duration_hours(self):
        if not self.ended_at:
            return 0
        duration = self.ended_at - self.started_at
        return round(duration.total_seconds() / 3600, 2)


class AttendanceReport(models.Model):
    week_start = models.DateField()
    week_end = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey('staff.Employee', on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.TextField(blank=True)

    def __str__(self) -> str:
        return f'Отчет {self.week_start} - {self.week_end}'


class AttendanceReportLine(models.Model):
    report = models.ForeignKey(AttendanceReport, on_delete=models.CASCADE, related_name='lines')
    employee = models.ForeignKey('staff.Employee', on_delete=models.CASCADE)
    expected_hours = models.DecimalField(max_digits=6, decimal_places=2)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2)
    delta_hours = models.DecimalField(max_digits=6, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)


class LeaveRequest(models.Model):
    VACATION = 'vacation'
    SICK = 'sick'
    UNPAID = 'unpaid'
    TYPES = [
        (VACATION, 'Отпуск'),
        (SICK, 'Больничный'),
        (UNPAID, 'Отпуск без содержания'),
    ]

    employee = models.ForeignKey('staff.Employee', on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=16, choices=TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    approved_by = models.ForeignKey(
        'staff.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    documents_provided = models.BooleanField(default=False)
    comment = models.TextField(blank=True)

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError('Дата окончания не может быть раньше начала')
        if (self.end_date - self.start_date) > timedelta(days=28) and self.leave_type == self.VACATION:
            raise ValidationError('Длительность отпуска свыше 28 дней недопустима без согласования ГК')
