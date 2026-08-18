from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.customers.views.vehicle_views import VehicleViewSet

router = DefaultRouter()
router.register(r'', VehicleViewSet, basename='vehicle')

urlpatterns = [
    path('', include(router.urls)),
]
