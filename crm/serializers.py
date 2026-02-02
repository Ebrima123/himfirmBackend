# crm/serializers.py
from rest_framework import serializers
from .models import Customer, Lead, SiteVisit, Allocation
from core.models import EmployeeProfile
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class LeadSerializer(serializers.ModelSerializer):
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source='customer',
        write_only=True
    )

    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=EmployeeProfile.objects.all(),
        source='assigned_to',
        write_only=True,
        required=False,
        allow_null=True
    )

    customer = CustomerSerializer(read_only=True)
    assigned_to = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id',
            'customer_id',
            'customer',
            'source',
            'status',
            'notes',
            'assigned_to_id',
            'assigned_to',
            'created_at',
        ]



class SiteVisitSerializer(serializers.ModelSerializer):
    lead = LeadSerializer(read_only=True)
    project = serializers.StringRelatedField()
    attended_by = serializers.StringRelatedField()

    class Meta:
        model = SiteVisit
        fields = '__all__'

class AllocationSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    project = serializers.StringRelatedField()

    class Meta:
        model = Allocation
        fields = '__all__'