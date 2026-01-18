# audit/views.py
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import AuditLog
from .serializers import AuditLogSerializer

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only endpoint for audit logs.
    Accessible only to authenticated users (further restricted by permissions/groups in future).
    Supports filtering and searching.
    """
    queryset = AuditLog.objects.all().select_related('user')
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

    # Filtering & Searching
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    filterset_fields = {
        'action': ['exact', 'in'],
        'model_name': ['exact', 'icontains'],
        'user__email': ['exact', 'icontains'],
        'timestamp': ['gte', 'lte', 'date'],
    }

    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'model_name',
        'action',
        'changes'
    ]

    ordering_fields = ['timestamp', 'action', 'model_name']
    ordering = ['-timestamp']  # Newest first