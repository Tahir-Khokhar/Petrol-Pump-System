from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.sales.views.refund_views import RefundViewSet
from apps.sales.views.sale_views import CreateSaleView, SaleViewSet, SaleReceiptView

router = DefaultRouter()
router.register(r'sales', SaleViewSet, basename='sale')
router.register(r'refunds', RefundViewSet, basename='refund')

urlpatterns = [
    # Custom routes BEFORE router to avoid UUID pattern collision
    path('create-sale/', CreateSaleView.as_view(), name='create-sale'),
    path('<uuid:uuid>/receipt/', SaleReceiptView.as_view(), name='sale-receipt'),
    path('', include(router.urls)),
]