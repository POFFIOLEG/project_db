from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


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
    auto_closed = models.BooleanField(default=False)

    def duration_hours(self):
        if not self.ended_at:
            return 0
        duration = self.ended_at - self.started_at
        return round(duration.total_seconds() / 3600, 2)


class EmployeeSchedule(models.Model):
    employee = models.OneToOneField('staff.Employee', on_delete=models.CASCADE, related_name='schedule_assignment')
    template = models.ForeignKey(ScheduleTemplate, on_delete=models.CASCADE, related_name='employee_assignments')
    effective_from = models.DateField()
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f'{self.employee.full_name} → {self.template.name}'


class AttendanceReport(models.Model):
    DRAFT = 'draft'
    SUBMITTED = 'submitted'
    APPROVED = 'approved'
    STATUSES = [
        (DRAFT, 'Черновик'),
        (SUBMITTED, 'На подтверждении'),
        (APPROVED, 'Подтверждён'),
    ]

    week_start = models.DateField()
    week_end = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        'staff.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_reports',
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey('staff.Employee', on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.TextField(blank=True)
    tolerance_minutes = models.PositiveIntegerField(default=30)
    status = models.CharField(max_length=16, choices=STATUSES, default=DRAFT)

    def __str__(self) -> str:
        return f'Отчет {self.week_start} - {self.week_end}'


class AttendanceReportLine(models.Model):
    report = models.ForeignKey(AttendanceReport, on_delete=models.CASCADE, related_name='lines')
    employee = models.ForeignKey('staff.Employee', on_delete=models.CASCADE)
    expected_hours = models.DecimalField(max_digits=6, decimal_places=2)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2)
    delta_hours = models.DecimalField(max_digits=6, decimal_places=2)
    approved_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    adjustment_reason = models.CharField(max_length=255, blank=True)
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
    documents_deadline = models.DateField(null=True, blank=True)

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError('Дата окончания не может быть раньше начала')
        if (self.end_date - self.start_date) > timedelta(days=28) and self.leave_type == self.VACATION:
            raise ValidationError('Длительность отпуска свыше 28 дней недопустима без согласования ГК')
        if self.leave_type == self.SICK and not self.documents_deadline:
            self.documents_deadline = self.end_date + timedelta(days=7)

    @property
    def requires_documents(self):
        return self.leave_type == self.SICK and not self.documents_provided and timezone.now().date() > (
            self.documents_deadline or self.end_date + timedelta(days=7)
        )
