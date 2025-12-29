# crm/admin.py
from django.contrib import admin
from .models import Customer, Lead, SiteVisit, Allocation

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'email', 'date_registered')
    search_fields = ('full_name', 'phone', 'email', 'national_id')
    list_filter = ('date_registered',)

class LeadInline(admin.TabularInline):
    model = Lead
    extra = 0
    readonly_fields = ('status', 'assigned_to')

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('customer', 'status', 'assigned_to', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer__full_name', 'customer__phone', 'assigned_to__user__email')
    raw_id_fields = ('assigned_to',)

@admin.register(SiteVisit)
class SiteVisitAdmin(admin.ModelAdmin):
    list_display = ('lead', 'project', 'visit_date', 'attended_by')
    list_filter = ('visit_date',)
    raw_id_fields = ('attended_by',)

@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    list_display = ('customer', 'project', 'plot_number', 'allocation_date', 'amount_paid', 'balance')
    search_fields = ('customer__full_name', 'plot_number', 'project__name')
    list_filter = ('allocation_date',)