from rest_framework import viewsets

from .models import AccessRole, Department, Employee, Position
from .serializers import AccessRoleSerializer, DepartmentSerializer, EmployeeSerializer, PositionSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer


class AccessRoleViewSet(viewsets.ModelViewSet):
    queryset = AccessRole.objects.all()
    serializer_class = AccessRoleSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related('user', 'department', 'position', 'role')
    serializer_class = EmployeeSerializer
