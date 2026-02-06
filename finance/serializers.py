# finance/serializers.py
from rest_framework import serializers
from .models import Invoice, Payment

class InvoiceSerializer(serializers.ModelSerializer):
    allocation = serializers.StringRelatedField()
    class Meta:
        model = Invoice
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.__str__', read_only=True)
    received_by_name = serializers.CharField(source='received_by.__str__', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'receipt_number', 'payment_date', 'amount', 'payment_method',
            'customer', 'customer_name',  # customer for write, customer_name for read
            'invoice', 
            'received_by', 'received_by_name'  # received_by for write, received_by_name for read
        ]