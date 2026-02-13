
# projects/filters.py
import django_filters
from django.db.models import Q
from .models import (
    LandParcel, Project, ProjectTask, ProjectExpense, ProjectPermit
)


class LandParcelFilter(django_filters.FilterSet):
    """Custom filters for LandParcel"""
    city = django_filters.CharFilter(lookup_expr='icontains')
    min_size = django_filters.NumberFilter(field_name='size_sq_meters', lookup_expr='gte')
    max_size = django_filters.NumberFilter(field_name='size_sq_meters', lookup_expr='lte')
    min_cost = django_filters.NumberFilter(field_name='acquisition_cost', lookup_expr='gte')
    max_cost = django_filters.NumberFilter(field_name='acquisition_cost', lookup_expr='lte')
    has_utilities = django_filters.BooleanFilter(method='filter_has_utilities')
    
    class Meta:
        model = LandParcel
        fields = {
            'status': ['exact', 'in'],
            'zoning': ['exact', 'in'],
            'location': ['exact', 'icontains'],
            'acquisition_date': ['exact', 'gte', 'lte'],
        }
    
    def filter_has_utilities(self, queryset, name, value):
        if value:
            return queryset.filter(
                has_water=True,
                has_electricity=True,
                has_sewage=True
            )
        return queryset


class ProjectFilter(django_filters.FilterSet):
    """Custom filters for Project"""
    manager = django_filters.NumberFilter(field_name='manager__id')
    min_budget = django_filters.NumberFilter(field_name='budget', lookup_expr='gte')
    max_budget = django_filters.NumberFilter(field_name='budget', lookup_expr='lte')
    start_date_from = django_filters.DateFilter(field_name='start_date', lookup_expr='gte')
    start_date_to = django_filters.DateFilter(field_name='start_date', lookup_expr='lte')
    completion_from = django_filters.DateFilter(field_name='expected_completion', lookup_expr='gte')
    completion_to = django_filters.DateFilter(field_name='expected_completion', lookup_expr='lte')
    is_delayed = django_filters.BooleanFilter(method='filter_delayed')
    
    class Meta:
        model = Project
        fields = {
            'status': ['exact', 'in'],
            'priority': ['exact', 'in'],
            'project_type': ['exact'],
            'land_parcel': ['exact'],
        }
    
    def filter_delayed(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(
                expected_completion__lt=timezone.now().date()
            ).exclude(status__in=['completed', 'cancelled'])
        return queryset.exclude(
            expected_completion__lt=timezone.now().date()
        )


class ProjectTaskFilter(django_filters.FilterSet):
    """Custom filters for ProjectTask"""
    assigned_to = django_filters.NumberFilter(field_name='assigned_to__id')
    created_by = django_filters.NumberFilter(field_name='created_by__id')
    due_date_from = django_filters.DateFilter(field_name='due_date', lookup_expr='gte')
    due_date_to = django_filters.DateFilter(field_name='due_date', lookup_expr='lte')
    is_overdue = django_filters.BooleanFilter(method='filter_overdue')
    is_approved = django_filters.BooleanFilter()
    
    class Meta:
        model = ProjectTask
        fields = {
            'project': ['exact'],
            'phase': ['exact'],
            'category': ['exact'],
            'status': ['exact', 'in'],
            'priority': ['exact', 'in'],
        }
    
    def filter_overdue(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(
                status__in=['pending', 'in_progress'],
                due_date__lt=timezone.now().date()
            )
        return queryset.exclude(
            status__in=['pending', 'in_progress'],
            due_date__lt=timezone.now().date()
        )


class ProjectExpenseFilter(django_filters.FilterSet):
    """Custom filters for ProjectExpense"""
    expense_date_from = django_filters.DateFilter(field_name='expense_date', lookup_expr='gte')
    expense_date_to = django_filters.DateFilter(field_name='expense_date', lookup_expr='lte')
    min_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    vendor = django_filters.CharFilter(field_name='vendor_name', lookup_expr='icontains')
    
    class Meta:
        model = ProjectExpense
        fields = {
            'project': ['exact'],
            'category': ['exact'],
            'expense_type': ['exact', 'in'],
            'payment_status': ['exact', 'in'],
        }


class ProjectPermitFilter(django_filters.FilterSet):
    """Custom filters for ProjectPermit"""
    expiry_date_from = django_filters.DateFilter(field_name='expiry_date', lookup_expr='gte')
    expiry_date_to = django_filters.DateFilter(field_name='expiry_date', lookup_expr='lte')
    
    class Meta:
        model = ProjectPermit
        fields = {
            'project': ['exact'],
            'permit_type': ['exact'],
            'status': ['exact', 'in'],
            'fee_paid': ['exact'],
        }