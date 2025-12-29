# support/serializers.py
from rest_framework import serializers
from .models import VisitorLog, Vehicle, IncidentReport
from core.models import EmployeeProfile

class VisitorLogSerializer(serializers.ModelSerializer):
    """
    Serializer for visitor logs (Receptionist primary use).
    """
    time_in_formatted = serializers.DateTimeField(source='time_in', format='%Y-%m-%d %H:%M', read_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = VisitorLog
        fields = ['id', 'full_name', 'phone', 'purpose', 'time_in', 'time_out', 'time_in_formatted', 'duration']
        read_only_fields = ['time_in']

    def get_duration(self, obj):
        if obj.time_out:
            delta = obj.time_out - obj.time_in
            hours, remainder = divmod(delta.seconds, 3600)
            minutes = remainder // 60
            return f"{hours}h {minutes}m"
        return "Still inside"


class VehicleSerializer(serializers.ModelSerializer):
    """
    Serializer for vehicle management (Drivers, Site & Logistics Supervisor).
    """
    assigned_driver = serializers.StringRelatedField(read_only=True)  # Optional future FK

    class Meta:
        model = Vehicle
        fields = '__all__'


class IncidentReportSerializer(serializers.ModelSerializer):
    """
    Serializer for security/maintenance incidents (Security, Janitor, Supervisors).
    """
    reported_by_name = serializers.CharField(source='reported_by.user.get_full_name', read_only=True)
    reported_by_email = serializers.CharField(source='reported_by.user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = IncidentReport
        fields = '__all__'