# audit/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet

# Create a router and register the AuditLog viewset
router = DefaultRouter()
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')

urlpatterns = [
    # Base path: /api/audit/
    # Examples:
    # GET    /api/audit/audit-logs/                  → List all logs (paginated)
    # GET    /api/audit/audit-logs/1/                → Retrieve single log
    # GET    /api/audit/audit-logs/?model_name=Project → Filter by model
    # GET    /api/audit/audit-logs/?action=DELETE     → Filter by action
    # GET    /api/audit/audit-logs/?user__email=ceo@himfirm3.com → By user
    path('', include(router.urls)),
]

# Optional: Add a custom endpoint for summary stats (future enhancement)
# path('summary/', AuditSummaryView.as_view(), name='audit-summary'),