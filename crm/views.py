# crm/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Customer, Lead, SiteVisit, Allocation
from .serializers import CustomerSerializer, LeadSerializer, SiteVisitSerializer, AllocationSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('-date_registered')
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all().order_by('-created_at')
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]

class SiteVisitViewSet(viewsets.ModelViewSet):
    queryset = SiteVisit.objects.all().order_by('-visit_date')
    serializer_class = SiteVisitSerializer
    permission_classes = [IsAuthenticated]

class AllocationViewSet(viewsets.ModelViewSet):
    queryset = Allocation.objects.all().order_by('-allocation_date')
    serializer_class = AllocationSerializer
    permission_classes = [IsAuthenticated]