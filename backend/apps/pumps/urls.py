from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.pumps.views.pump_views import (
    PumpAssignEmployeeView,
    PumpStatusUpdateView,
    PumpViewSet,
)

router = DefaultRouter()
router.register(r'', PumpViewSet, basename='pump')

urlpatterns = [
    # Custom routes MUST come before the router include
    # because 'assign-employee' matches the router's uuid detail pattern
    path('assign-employee/', PumpAssignEmployeeView.as_view(), name='pump-assign-employee'),
    path('update-status/', PumpStatusUpdateView.as_view(), name='pump-update-status'),
    path('', include(router.urls)),
]
