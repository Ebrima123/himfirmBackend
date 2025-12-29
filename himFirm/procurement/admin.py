# procurement/admin.py
from django.contrib import admin
from .models import Supplier, PurchaseOrder

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email')
    search_fields = ('name', 'contact_person', 'phone', 'email')

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'supplier', 'total_amount', 'status', 'order_date')
    list_filter = ('status', 'order_date')
    search_fields = ('po_number', 'supplier__name')
    readonly_fields = ('order_date', 'po_number')