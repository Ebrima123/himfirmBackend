# core/serializers.py
from rest_framework import serializers
from .models import EmployeeProfile, Department

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class EmployeeProfileSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = ['id','position', 'department', 'phone', 'full_name', 'username']