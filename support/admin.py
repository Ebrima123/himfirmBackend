# support/admin.py
from django.contrib import admin
from .models import VisitorLog, Vehicle, IncidentReport

@admin.register(VisitorLog)
class VisitorLogAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'purpose', 'time_in', 'time_out')
    list_filter = ('time_in',)
    search_fields = ('full_name', 'phone', 'purpose')
    date_hierarchy = 'time_in'

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('registration', 'model')
    search_fields = ('registration', 'model')

@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ('incident_type', 'reported_by', 'status')
    list_filter = ('status', 'incident_type')
    search_fields = ('description', 'incident_type')