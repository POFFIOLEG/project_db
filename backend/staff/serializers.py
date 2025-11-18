from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import AccessRole, Department, Employee, Position

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = '__all__'


class AccessRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessRole
        fields = '__all__'


class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source='user'
    )

    class Meta:
        model = Employee
        fields = [
            'id',
            'user',
            'user_id',
            'full_name',
            'passport_series',
            'passport_number',
            'passport_address',
            'foreign_passport',
            'birth_date',
            'department',
            'position',
            'work_phone',
            'personal_phone',
            'work_email',
            'personal_email',
            'role',
            'status',
            'hired_at',
            'fired_at',
        ]

