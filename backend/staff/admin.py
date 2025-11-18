from django.contrib import admin

from .models import AccessRole, Department, Employee, Position


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'monthly_hours', 'hourly_rate')


@admin.register(AccessRole)
class AccessRoleAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'department', 'position', 'status')
    list_filter = ('status', 'department')
