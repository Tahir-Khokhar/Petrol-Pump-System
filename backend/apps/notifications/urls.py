from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.notifications.views.notification_views import (
    NotificationViewSet,
    mark_all_read,
    unread_count,
)

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    path('mark-all-read/', mark_all_read, name='notification-mark-all-read'),
    path('unread-count/', unread_count, name='notification-unread-count'),
    path('', include(router.urls)),
]
