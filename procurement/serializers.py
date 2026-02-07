# procurement/serializers.py
from rest_framework import serializers
from .models import Supplier, PurchaseOrder

class SupplierSerializer(serializers.ModelSerializer):
    po_count = serializers.IntegerField(source='purchase_orders.count', read_only=True)

    class Meta:
        model = Supplier
        fields = '__all__'

class PurchaseOrderSerializer(serializers.ModelSerializer):
    # Read-only fields for display
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    supplier_phone = serializers.CharField(source='supplier.phone', read_only=True)
    approved_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'order_date', 'delivery_date', 'total_amount', 'status',
            'supplier', 'supplier_name', 'supplier_phone',  # supplier for write, supplier_name/phone for read
            'items', 'notes',
            'approved_by', 'approved_by_name', 'approved_at'  # approved_by for write, approved_by_name for read
        ]
        read_only_fields = ['po_number', 'order_date', 'approved_at']

    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return obj.approved_by.user.get_full_name() or obj.approved_by.user.username
        return 'Not approved'