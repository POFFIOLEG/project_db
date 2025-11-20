from datetime import date, timedelta

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    AttendanceReport,
    AttendanceReportLine,
    EmployeeSchedule,
    LeaveRequest,
    ScheduleTemplate,
    WorkSession,
)
from .serializers import (
    AttendanceReportLineSerializer,
    AttendanceReportSerializer,
    EmployeeScheduleSerializer,
    LeaveRequestSerializer,
    ScheduleTemplateSerializer,
    WorkSessionSerializer,
)
from .services import AttendanceReportService, WorkSessionService


class ScheduleTemplateViewSet(viewsets.ModelViewSet):
    queryset = ScheduleTemplate.objects.select_related('position').all()
    serializer_class = ScheduleTemplateSerializer


class WorkSessionViewSet(viewsets.ModelViewSet):
    queryset = WorkSession.objects.select_related('employee')
    serializer_class = WorkSessionSerializer
    filterset_fields = ['employee']

    @action(detail=False, methods=['post'])
    def close_overdue(self, request):
        closed = WorkSessionService.close_overdue_sessions()
        return Response({'closed_sessions': closed})


class AttendanceReportViewSet(viewsets.ModelViewSet):
    queryset = AttendanceReport.objects.prefetch_related('lines')
    serializer_class = AttendanceReportSerializer
    filterset_fields = ['status', 'week_start']

    @action(detail=False, methods=['post'])
    def generate_weekly(self, request):
        week_start_str = request.data.get('week_start')
        if week_start_str:
            week_start = date.fromisoformat(week_start_str)
        else:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
        employee = getattr(request.user, 'employee', None)
        tolerance = int(request.data.get('tolerance_minutes', 30))
        service = AttendanceReportService(week_start, generated_by=employee, tolerance_minutes=tolerance)
        report = service.generate()
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        report = self.get_object()
        service = AttendanceReportService(report.week_start)
        service.submit(report)
        return Response(self.get_serializer(report).data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        report = self.get_object()
        employee = getattr(request.user, 'employee', None)
        if not employee:
            return Response({'detail': 'Требуется сотрудник-утверждающий'}, status=status.HTTP_400_BAD_REQUEST)
        comment = request.data.get('comment', '')
        AttendanceReportService(report.week_start).approve(report, employee, comment)
        return Response(self.get_serializer(report).data)


class AttendanceReportLineViewSet(viewsets.ModelViewSet):
    queryset = AttendanceReportLine.objects.select_related('report', 'employee')
    serializer_class = AttendanceReportLineSerializer
    filterset_fields = ['report', 'employee']


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.select_related('employee')
    serializer_class = LeaveRequestSerializer
    filterset_fields = ['leave_type', 'employee']


class EmployeeScheduleViewSet(viewsets.ModelViewSet):
    queryset = EmployeeSchedule.objects.select_related('employee', 'template')
    serializer_class = EmployeeScheduleSerializer
    filterset_fields = ['employee', 'template']
