# core/serializers.py
from rest_framework import serializers
from .models import EmployeeProfile, Department , CustomUser

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class EmployeeProfileSerializer(serializers.ModelSerializer):
    # Read-only nested output
    department = DepartmentSerializer(read_only=True)

    full_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    # Writable fields
    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )

    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        write_only=True,
        required=False,
        allow_null=True,
    )

    reports_to = serializers.PrimaryKeyRelatedField(
        queryset=EmployeeProfile.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = EmployeeProfile
        fields = [
            'id',
            'user',
            'position',
            'phone',

            # writable
            'department_id',
            'reports_to',
            'is_active',
            'date_joined',

            # read-only
            'department',
            'full_name',
            'username',
        ]
