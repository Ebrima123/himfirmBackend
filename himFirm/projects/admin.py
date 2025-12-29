# projects/admin.py
from django.contrib import admin
from .models import LandParcel, Project, ProjectTask

@admin.register(LandParcel)
class LandParcelAdmin(admin.ModelAdmin):
    list_display = ('title_number', 'location', 'size_sq_meters', 'status', 'acquisition_date')
    list_filter = ('status', 'acquisition_date')
    search_fields = ('title_number', 'location')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'land_parcel', 'manager', 'status', 'start_date')
    list_filter = ('status', 'start_date')
    search_fields = ('name', 'land_parcel__title_number', 'manager__user__email')
    raw_id_fields = ('manager',)

class ProjectTaskInline(admin.TabularInline):
    model = ProjectTask
    extra = 1
    raw_id_fields = ('assigned_to',)

@admin.register(ProjectTask)
class ProjectTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'assigned_to', 'status', 'due_date')
    list_filter = ('status', 'due_date')
    search_fields = ('title', 'project__name', 'assigned_to__user__email')
    raw_id_fields = ('assigned_to',)