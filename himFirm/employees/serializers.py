# employees/serializers.py
from rest_framework import serializers
from .models import LeaveRequest

class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)
    employee_email = serializers.CharField(source='employee.user.email', read_only=True)
    employee_position = serializers.CharField(source='employee.position', read_only=True)
    employee_department = serializers.CharField(source='employee.department.name', read_only=True, default='')
    reviewer_name = serializers.CharField(source='reviewed_by.user.get_full_name', read_only=True, default='Not reviewed')
    reviewer_email = serializers.CharField(source='reviewed_by.user.email', read_only=True, default='')
    duration_days = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name', 'employee_email', 'employee_position', 'employee_department',
            'start_date', 'end_date', 'reason', 'status', 'requested_at',
            'reviewed_at', 'reviewed_by', 'reviewer_name', 'reviewer_email', 'duration_days'
        ]
        read_only_fields = ['requested_at', 'reviewed_at', 'reviewed_by', 'reviewer_name', 'reviewer_email']

    def get_duration_days(self, obj):
        return (obj.end_date - obj.start_date).days + 1