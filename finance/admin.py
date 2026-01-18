# finance/admin.py
from django.contrib import admin
from .models import Invoice, Payment

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'allocation', 'amount', 'paid_amount', 'status', 'due_date')
    list_filter = ('status', 'due_date')
    search_fields = ('invoice_number', 'allocation__customer__full_name')
    readonly_fields = ('issue_date',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'customer', 'amount', 'payment_date', 'payment_method')
    list_filter = ('payment_date', 'payment_method')
    search_fields = ('receipt_number', 'customer__full_name')