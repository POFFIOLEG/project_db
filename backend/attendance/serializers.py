from rest_framework import serializers

from .models import (
    AttendanceReport,
    AttendanceReportLine,
    EmployeeSchedule,
    LeaveRequest,
    ScheduleTemplate,
    WorkSession,
)


class ScheduleTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleTemplate
        fields = '__all__'


class WorkSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkSession
        fields = '__all__'


class EmployeeScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeSchedule
        fields = '__all__'


class AttendanceReportLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceReportLine
        fields = '__all__'


class AttendanceReportSerializer(serializers.ModelSerializer):
    lines = AttendanceReportLineSerializer(many=True, read_only=True)

    class Meta:
        model = AttendanceReport
        fields = '__all__'


class LeaveRequestSerializer(serializers.ModelSerializer):
    requires_documents = serializers.BooleanField(read_only=True)

    class Meta:
        model = LeaveRequest
        fields = '__all__'

