from django.contrib import admin

from .models import (
    AttendanceReport,
    AttendanceReportLine,
    EmployeeSchedule,
    LeaveRequest,
    ScheduleTemplate,
    WorkSession,
)


@admin.register(ScheduleTemplate)
class ScheduleTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'position')


@admin.register(WorkSession)
class WorkSessionAdmin(admin.ModelAdmin):
    list_display = ('employee', 'started_at', 'ended_at', 'source', 'auto_closed')
    list_filter = ('source', 'auto_closed')


class AttendanceReportLineInline(admin.TabularInline):
    model = AttendanceReportLine
    extra = 0


@admin.register(AttendanceReport)
class AttendanceReportAdmin(admin.ModelAdmin):
    list_display = ('week_start', 'week_end', 'status', 'approved_at')
    list_filter = ('status',)
    inlines = [AttendanceReportLineInline]


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'documents_provided', 'documents_deadline')
    list_filter = ('leave_type', 'documents_provided')


@admin.register(EmployeeSchedule)
class EmployeeScheduleAdmin(admin.ModelAdmin):
    list_display = ('employee', 'template', 'effective_from')
