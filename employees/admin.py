# employees/admin.py
from django.contrib import admin
from .models import LeaveRequest

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'start_date', 'end_date', 'status', 'requested_at')
    list_filter = ('status', 'start_date', 'employee__department')
    search_fields = ('employee__user__email', 'employee__user__first_name', 'reason')
    raw_id_fields = ('employee', 'reviewed_by')
    readonly_fields = ('requested_at',)