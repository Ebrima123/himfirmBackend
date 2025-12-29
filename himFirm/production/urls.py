# production/urls.py
from rest_framework.routers import DefaultRouter
from .views import RawMaterialViewSet, ProductionBatchViewSet, BrickStockViewSet, DeliveryViewSet

router = DefaultRouter()
router.register(r'materials', RawMaterialViewSet)
router.register(r'batches', ProductionBatchViewSet)
router.register(r'stock', BrickStockViewSet)
router.register(r'deliveries', DeliveryViewSet)

urlpatterns = router.urls