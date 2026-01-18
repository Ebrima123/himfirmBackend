# support/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    VisitorLogViewSet,
    VehicleViewSet,
    IncidentReportViewSet
)

router = DefaultRouter()
router.register(r'visitors', VisitorLogViewSet, basename='visitorlog')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'incidents', IncidentReportViewSet, basename='incident')

# Use router.urls directly instead of include(router.urls)
urlpatterns = router.urls

# If you need to add custom paths later, do it like this:
# urlpatterns = [
#     *router.urls,  # Unpack router URLs
#     path('visitors/check-out/', VisitorCheckOutView.as_view(), name='visitor_checkout'),
# ]