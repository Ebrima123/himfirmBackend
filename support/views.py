# support/views.py
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import VisitorLog, Vehicle, IncidentReport
from .serializers import (
    VisitorLogSerializer,
    VehicleSerializer,
    IncidentReportSerializer
)

class VisitorLogViewSet(viewsets.ModelViewSet):
    """
    API for visitor management (Receptionist, Admin & Records Manager, Security).
    Receptionist: Create logs | Security: Check-out | Managers: Reports
    """
    queryset = VisitorLog.objects.all().order_by('-time_in')
    serializer_class = VisitorLogSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    filterset_fields = ['full_name', 'phone']
    search_fields = ['full_name', 'phone', 'purpose']
    ordering_fields = ['time_in', 'time_out']
    ordering = ['-time_in']

    def get_queryset(self):
        """
        Role-based filtering:
        - Receptionist/Security: Today's visitors
        - Managers: All (with filters)
        """
        qs = super().get_queryset()
        user_profile = self.request.user.profile
        if user_profile.position in ['Receptionist', 'Security']:
            return qs.filter(time_in__date=self.request.query_params.get('today', timezone.now().date()))
        return qs


class VehicleViewSet(viewsets.ModelViewSet):
    """
    API for fleet management (Drivers, Site & Logistics Supervisor, Production Manager).
    """
    queryset = Vehicle.objects.all().order_by('registration')
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['registration', 'model']
    ordering_fields = ['registration']


class IncidentReportViewSet(viewsets.ModelViewSet):
    """
    API for security/maintenance incidents (Security, Janitor, Supervisors).
    """
    queryset = IncidentReport.objects.all().select_related('reported_by').order_by('-id')
    serializer_class = IncidentReportSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    filterset_fields = ['status', 'incident_type', 'reported_by__user__email']
    search_fields = ['description', 'incident_type', 'reported_by__user__first_name']
    ordering_fields = ['status', 'incident_type']
    ordering = ['-id']

    def get_queryset(self):
        """
        Security/Janitor: Their reports + open incidents
        Supervisors/Managers: All incidents
        """
        qs = super().get_queryset()
        profile = self.request.user.profile
        if profile.position in ['Security', 'Janitor']:
            return qs.filter(Q(reported_by=profile) | Q(status='open'))
        return qs