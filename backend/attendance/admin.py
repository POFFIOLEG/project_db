from django.contrib import admin

from .models import AttendanceReport, AttendanceReportLine, LeaveRequest, ScheduleTemplate, WorkSession


@admin.register(ScheduleTemplate)
class ScheduleTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'position')


@admin.register(WorkSession)
class WorkSessionAdmin(admin.ModelAdmin):
    list_display = ('employee', 'started_at', 'ended_at', 'source')


class AttendanceReportLineInline(admin.TabularInline):
    model = AttendanceReportLine
    extra = 0


@admin.register(AttendanceReport)
class AttendanceReportAdmin(admin.ModelAdmin):
    list_display = ('week_start', 'week_end', 'approved_at')
    inlines = [AttendanceReportLineInline]


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'documents_provided')
