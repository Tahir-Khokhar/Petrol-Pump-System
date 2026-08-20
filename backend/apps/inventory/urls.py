from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.inventory.views.inventory_views import (
    InventoryItemViewSet,
    InventoryTransactionViewSet,
    LowStockListView,
    StockAdjustmentView,
)

router = DefaultRouter()
router.register(r'items', InventoryItemViewSet, basename='inventory-item')
router.register(r'transactions', InventoryTransactionViewSet, basename='inventory-transaction')

urlpatterns = [
    # Custom routes BEFORE router to avoid UUID pattern collision
    path('stock-adjust/', StockAdjustmentView.as_view(), name='stock-adjust'),
    path('low-stock/', LowStockListView.as_view(), name='low-stock'),
    path('', include(router.urls)),
]
