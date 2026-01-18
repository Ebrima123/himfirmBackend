# production/views.py
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import RawMaterial, ProductionBatch, BrickStock, Delivery
from .serializers import (
    RawMaterialSerializer,
    ProductionBatchSerializer,
    BrickStockSerializer,
    DeliverySerializer
)

class RawMaterialViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing raw materials used in brick production.
    Accessible to Production & Depot Manager and Procurement.
    """
    queryset = RawMaterial.objects.all().order_by('name')
    serializer_class = RawMaterialSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    search_fields = ['name', 'unit']
    ordering_fields = ['current_stock', 'reorder_level', 'name']
    ordering = ['name']

    def get_queryset(self):
        """
        Highlight materials below reorder level for quick attention.
        """
        qs = super().get_queryset()
        # Optional: Add annotation for low stock flag if needed in frontend
        return qs


class ProductionBatchViewSet(viewsets.ModelViewSet):
    """
    API endpoint for brick production batches (core of BWU Unit).
    Used by Production Manager and Block Officer for quality control.
    """
    queryset = ProductionBatch.objects.all().select_related('inspected_by').order_by('-production_date')
    serializer_class = ProductionBatchSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    filterset_fields = ['quality_status', 'production_date']
    search_fields = ['batch_number', 'notes']
    ordering_fields = ['production_date', 'bricks_produced', 'quality_status']
    ordering = ['-production_date']


class BrickStockViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tracking brick inventory in warehouse and sites.
    """
    queryset = BrickStock.objects.all().select_related('batch').order_by('-batch__production_date')
    serializer_class = BrickStockSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    filterset_fields = ['location', 'batch__quality_status']
    search_fields = ['batch__batch_number', 'location']
    ordering_fields = ['quantity', 'location']
    ordering = ['-quantity']


class DeliveryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for brick deliveries to projects/sites.
    Used by Delivery Officer, Driver, and Project Supervisor.
    """
    queryset = Delivery.objects.all().select_related(
        'batch', 'project', 'driver', 'received_by'
    ).order_by('-delivery_date')
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    filterset_fields = {
        'project__id': ['exact'],
        'project__name': ['icontains'],
        'delivery_date': ['exact', 'gte', 'lte'],
        'driver__user__email': ['exact'],
        'received_by__user__email': ['exact'],
    }
    search_fields = ['batch__batch_number', 'project__name']
    ordering_fields = ['delivery_date', 'quantity']
    ordering = ['-delivery_date']

    def get_queryset(self):
        """
        Optional: Restrict drivers to see only their deliveries
        (Uncomment when role-based filtering is active)
        """
        user = self.request.user
        profile = user.profile if hasattr(user, 'profile') else None
        if profile and profile.position == 'Driver':
            return self.queryset.filter(driver=profile)
        return super().get_queryset()