# projects/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LandParcelViewSet, ProjectViewSet, ProjectTaskViewSet

router = DefaultRouter()
router.register(r'land-parcels', LandParcelViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'tasks', ProjectTaskViewSet)

urlpatterns = [
    path('', include(router.urls)),
]