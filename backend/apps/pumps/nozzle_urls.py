from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.pumps.views.nozzle_views import (
    NozzleMeterUpdateView,
    NozzleViewSet,
)

router = DefaultRouter()
router.register(r'', NozzleViewSet, basename='nozzle')

urlpatterns = [
    # Custom routes MUST come before the router include
    # because 'update-meter' matches the router's uuid detail pattern
    path('update-meter/', NozzleMeterUpdateView.as_view(), name='nozzle-update-meter'),
    path('', include(router.urls)),
]
