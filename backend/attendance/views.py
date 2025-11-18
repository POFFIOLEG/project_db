from rest_framework import viewsets

from .models import AttendanceReport, AttendanceReportLine, LeaveRequest, ScheduleTemplate, WorkSession
from .serializers import (
    AttendanceReportLineSerializer,
    AttendanceReportSerializer,
    LeaveRequestSerializer,
    ScheduleTemplateSerializer,
    WorkSessionSerializer,
)


class ScheduleTemplateViewSet(viewsets.ModelViewSet):
    queryset = ScheduleTemplate.objects.select_related('position').all()
    serializer_class = ScheduleTemplateSerializer


class WorkSessionViewSet(viewsets.ModelViewSet):
    queryset = WorkSession.objects.select_related('employee')
    serializer_class = WorkSessionSerializer
    filterset_fields = ['employee']


class AttendanceReportViewSet(viewsets.ModelViewSet):
    queryset = AttendanceReport.objects.prefetch_related('lines')
    serializer_class = AttendanceReportSerializer


class AttendanceReportLineViewSet(viewsets.ModelViewSet):
    queryset = AttendanceReportLine.objects.select_related('report', 'employee')
    serializer_class = AttendanceReportLineSerializer


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.select_related('employee')
    serializer_class = LeaveRequestSerializer
    filterset_fields = ['leave_type', 'employee']
