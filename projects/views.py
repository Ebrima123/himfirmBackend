# projects/views.py
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated , AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import LandParcel, Project, ProjectTask
from .serializers import (
    LandParcelSerializer,
    ProjectSerializer,
    ProjectTaskSerializer
)


class LandParcelViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing land parcels (acquisition & development bank).
    Accessible to PMDC Manager, Project Supervisors, CEO/EDBO.
    """
    queryset = LandParcel.objects.all().select_related().order_by('-acquisition_date')
    serializer_class = LandParcelSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    filterset_fields = ['status', 'location']
    search_fields = ['title_number', 'location']
    ordering_fields = ['acquisition_date', 'size_sq_meters', 'acquisition_cost']
    ordering = ['-acquisition_date']


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for real estate development projects.
    Core module for PMDC Manager and PPD Unit.
    """
    queryset = Project.objects.all().select_related('land_parcel', 'manager').prefetch_related('tasks').order_by(
        '-start_date')
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    filterset_fields = ['status', 'land_parcel__status', 'manager__user__email']
    search_fields = ['name', 'description', 'land_parcel__title_number', 'land_parcel__location']
    ordering_fields = ['start_date', 'expected_completion', 'budget', 'status']
    ordering = ['-start_date']

    def perform_create(self, serializer):
        # Optional: Auto-assign current user as manager if not specified
        if not serializer.validated_data.get('manager'):
            profile = self.request.user.profile
            if profile.position in ['PMDC Manager', 'Project Supervisor']:
                serializer.save(manager=profile)
        serializer.save()


class ProjectTaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tasks within projects.
    Used by Project Supervisors and assigned team members.
    """
    permission_classes = [AllowAny]
    queryset = ProjectTask.objects.all().select_related('project', 'assigned_to').order_by('-due_date')
    serializer_class = ProjectTaskSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    filterset_fields = ['status', 'project__id', 'assigned_to__user__email']
    search_fields = ['title', 'description', 'project__name']
    ordering_fields = ['due_date', 'status']
    ordering = ['due_date']

    def get_queryset(self):
        """
        Optional enhancement: Restrict tasks to user's assigned or managed projects
        (Uncomment when role-based filtering is needed)
        """
        user = self.request.user
        if user.profile.position in ['PMDC Manager', 'Project Supervisor']:
            return self.queryset
        # For regular assignees: show only their tasks
        return self.queryset.filter(assigned_to=user.profile)


from django.shortcuts import render

# Create your views here.
