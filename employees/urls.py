# employees/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeProfileViewSet, LeaveRequestViewSet
from core.views import DepartmentViewSet

router = DefaultRouter()
router.register(r'employees', EmployeeProfileViewSet, basename='employee')
router.register(r'leave-requests', LeaveRequestViewSet, basename='leaverequest')
router.register(r'departments', DepartmentViewSet, basename='department')

urlpatterns = [
    path('', include(router.urls)),
]