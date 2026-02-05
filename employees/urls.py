# employees/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeProfileViewSet, LeaveRequestViewSet

router = DefaultRouter()
router.register(r'employees', EmployeeProfileViewSet, basename='employee')
router.register(r'leave-requests', LeaveRequestViewSet, basename='leaverequest')

urlpatterns = [
    path('', include(router.urls)),
]