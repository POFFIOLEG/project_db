from django.conf import settings
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Position(models.Model):
    name = models.CharField(max_length=128, unique=True)
    monthly_hours = models.PositiveIntegerField(default=160)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    responsibilities = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class AccessRole(models.Model):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Employee(models.Model):
    ACTIVE = 'active'
    FIRED = 'fired'
    ON_LEAVE = 'leave'
    STATUSES = [
        (ACTIVE, 'Работает'),
        (FIRED, 'Уволен'),
        (ON_LEAVE, 'В отпуске/отсутствует'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee')
    full_name = models.CharField(max_length=255)
    passport_series = models.CharField(max_length=16, blank=True)
    passport_number = models.CharField(max_length=16, blank=True)
    passport_address = models.TextField(blank=True)
    foreign_passport = models.CharField(max_length=32, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)
    work_phone = models.CharField(max_length=32, blank=True)
    personal_phone = models.CharField(max_length=32, blank=True)
    work_email = models.EmailField(blank=True)
    personal_email = models.EmailField(blank=True)
    role = models.ForeignKey(AccessRole, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUSES, default=ACTIVE)
    hired_at = models.DateField(null=True, blank=True)
    fired_at = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        return self.full_name
