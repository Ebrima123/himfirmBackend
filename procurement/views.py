# procurement/views.py
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Supplier, PurchaseOrder
from .serializers import SupplierSerializer, PurchaseOrderSerializer

class SupplierViewSet(viewsets.ModelViewSet):
    """
    API for managing suppliers (Procurement & Purchasing Manager primary use).
    """
    queryset = Supplier.objects.all().filter(is_active=True).order_by('name')
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'contact_person', 'phone', 'email']
    ordering_fields = ['name', 'date_added']
    ordering = ['name']


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    API for purchase orders (P&D Unit).
    - Procurement Manager: Full access
    - Production Manager: View relevant POs
    - Finance: View for budgeting
    """
    queryset = PurchaseOrder.objects.all().select_related('supplier', 'approved_by__user').order_by('-order_date')
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'status': ['exact', 'in'],
        'supplier__id': ['exact'],
        'order_date': ['exact', 'gte', 'lte'],
        'expected_delivery_date': ['exact', 'gte', 'lte'],
    }
    search_fields = ['po_number', 'supplier__name', 'notes']
    ordering_fields = ['order_date', 'total_amount', 'status']
    ordering = ['-order_date']

    def get_queryset(self):
        profile = self.request.user.profile
        if profile.position == 'Procurement & Purchasing Manager':
            return self.queryset
        if profile.position in ['Production Manager', 'Finance Manager', 'EDBO', 'CEO']:
            return self.queryset
        # Others: limited or none
        return self.queryset.filter(status='approved')  # Only approved POs visible

    def perform_update(self, serializer):
        # Only Procurement Manager can approve/reject
        if 'status' in serializer.validated_data:
            new_status = serializer.validated_data['status']
            if new_status in ['approved', 'rejected']:
                if self.request.user.profile.position != 'Procurement & Purchasing Manager':
                    raise serializers.ValidationError("Only Procurement Manager can approve/reject POs.")
                serializer.save(
                    approved_by=self.request.user.profile,
                    approved_at=timezone.now()
                )
                return
        super().perform_update(serializer)