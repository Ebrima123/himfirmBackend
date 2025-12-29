# production/serializers.py
from rest_framework import serializers
from .models import RawMaterial, ProductionBatch, BrickStock, Delivery

class RawMaterialSerializer(serializers.ModelSerializer):
    low_stock = serializers.SerializerMethodField()

    class Meta:
        model = RawMaterial
        fields = '__all__'

    def get_low_stock(self, obj):
        return obj.current_stock < obj.reorder_level


class ProductionBatchSerializer(serializers.ModelSerializer):
    inspected_by_name = serializers.CharField(source='inspected_by.user.get_full_name', read_only=True)

    class Meta:
        model = ProductionBatch
        fields = '__all__'


class BrickStockSerializer(serializers.ModelSerializer):
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    production_date = serializers.DateField(source='batch.production_date', read_only=True)
    quality_status = serializers.CharField(source='batch.quality_status', read_only=True)

    class Meta:
        model = BrickStock
        fields = '__all__'


class DeliverySerializer(serializers.ModelSerializer):
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    driver_name = serializers.CharField(source='driver.user.get_full_name', read_only=True)
    received_by_name = serializers.CharField(source='received_by.user.get_full_name', read_only=True)

    class Meta:
        model = Delivery
        fields = '__all__'