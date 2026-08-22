from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.shifts.views.shift_views import CloseShiftView, OpenShiftView, ShiftViewSet

router = DefaultRouter()
router.register(r'shifts', ShiftViewSet, basename='shift')

urlpatterns = [
    # Custom routes BEFORE router to avoid UUID pattern collision
    path('open/', OpenShiftView.as_view(), name='open-shift'),
    path('close/<uuid:uuid>/', CloseShiftView.as_view(), name='close-shift'),
    path('', include(router.urls)),
]