# audit/serializers.py
from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)  # Shows email or full name
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True, default='')

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_email', 'user_full_name',
            'action', 'model_name', 'object_id',
            'timestamp', 'changes'
        ]
        read_only_fields = fields  # Audit logs should be read-only