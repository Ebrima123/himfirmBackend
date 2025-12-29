# documents/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, DocumentTypeViewSet

router = DefaultRouter()
router.register(r'files', DocumentViewSet)
router.register(r'types', DocumentTypeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('related/<str:model>/<int:pk>/', DocumentViewSet.as_view({'get': 'list'}), name='related-documents'),  # Optional: filter by model
]