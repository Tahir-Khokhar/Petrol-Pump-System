from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.fuel.views.fuel_type_views import (
    FuelTypeViewSet,
    FuelPriceHistoryViewSet,
    FuelPriceUpdateView,
)

router = DefaultRouter()
router.register(r'fuel-types', FuelTypeViewSet, basename='fuel-type')
router.register(r'price-history', FuelPriceHistoryViewSet, basename='fuel-price-history')

urlpatterns = [
    path('', include(router.urls)),
    path('update-price/', FuelPriceUpdateView.as_view(), name='fuel-price-update'),
]
