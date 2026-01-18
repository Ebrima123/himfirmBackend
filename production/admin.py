# production/admin.py
from django.contrib import admin
from .models import RawMaterial, ProductionBatch, BrickStock, Delivery

@admin.register(RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'current_stock', 'reorder_level', 'unit')
    search_fields = ('name',)
    list_filter = ('unit',)

@admin.register(ProductionBatch)
class ProductionBatchAdmin(admin.ModelAdmin):
    list_display = ('batch_number', 'production_date', 'bricks_produced', 'quality_status', 'inspected_by')
    list_filter = ('quality_status', 'production_date')
    search_fields = ('batch_number',)

@admin.register(BrickStock)
class BrickStockAdmin(admin.ModelAdmin):
    list_display = ('batch', 'quantity', 'location')
    search_fields = ('batch__batch_number', 'location')

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('batch', 'project', 'quantity', 'delivery_date', 'driver')
    list_filter = ('delivery_date',)
    raw_id_fields = ('driver', 'received_by')