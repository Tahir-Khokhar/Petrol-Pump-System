from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.shifts.views.meter_views import MeterReadingViewSet

router = DefaultRouter()
router.register(r'meter-readings', MeterReadingViewSet, basename='meter-reading')

urlpatterns = [
    path('', include(router.urls)),
]