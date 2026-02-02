# crm/serializers.py
from rest_framework import serializers
from .models import Customer, Lead, SiteVisit, Allocation

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
    customer = CustomerSerializer(read_only=True)

    assigned_to = serializers.StringRelatedField()
 

    class Meta:
        model = Lead
        fields = '__all__'

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