from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.fuel.views.tank_views import TankViewSet, TankStockAdjustmentView

router = DefaultRouter()
router.register(r'tanks', TankViewSet, basename='tank')

urlpatterns = [
    path('', include(router.urls)),
    path('adjust-stock/', TankStockAdjustmentView.as_view(), name='tank-stock-adjustment'),
]
