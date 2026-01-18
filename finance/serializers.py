# finance/serializers.py
from rest_framework import serializers
from .models import Invoice, Payment

class InvoiceSerializer(serializers.ModelSerializer):
    allocation = serializers.StringRelatedField()
    class Meta:
        model = Invoice
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    customer = serializers.StringRelatedField()
    received_by = serializers.StringRelatedField()
    class Meta:
        model = Payment
        fields = '__all__'



