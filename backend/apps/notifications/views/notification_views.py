from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.notifications.filters import NotificationFilter
from apps.notifications.models import Notification
from apps.notifications.permissions import IsNotificationOwner
from apps.notifications.serializers.notification_serializers import (
    NotificationListSerializer,
    NotificationSerializer,
)


class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Users can only see their own notifications."""

    permission_classes = [IsAuthenticated]
    filterset_class = NotificationFilter
    ordering_fields = ['created_at']

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return NotificationSerializer
        return NotificationListSerializer

    def get_paginated_response(self, data):
        """Override to wrap pagination in standard response format."""
        paginator = self.paginator
        return Response({
            'success': True,
            'message': 'Notifications retrieved successfully.',
            'data': {
                'count': paginator.page.paginator.count,
                'next': paginator.get_next_link(),
                'previous': paginator.get_previous_link(),
                'results': data,
            },
        }, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Notifications retrieved successfully.',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary='Mark notification as read',
        responses={200: NotificationSerializer},
    )
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        self.check_object_permissions(request, notification)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        serializer = NotificationSerializer(notification)
        return Response({
            'success': True,
            'message': 'Notification marked as read.',
            'data': serializer.data,
        })

    def get_permissions(self):
        if self.action in ('retrieve', 'mark_read'):
            return [IsAuthenticated(), IsNotificationOwner()]
        return [IsAuthenticated()]


@extend_schema(
    summary='Mark all notifications as read',
    responses={200: {}},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_read(request):
    """Mark all notifications for the authenticated user as read."""
    Notification.objects.filter(
        user=request.user, is_read=False,
    ).update(is_read=True)
    return Response({
        'success': True,
        'message': 'All notifications marked as read.',
    })


@extend_schema(
    summary='Get unread notification count',
    responses={200: {}},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_count(request):
    """Return the count of unread notifications for the authenticated user."""
    count = Notification.objects.filter(
        user=request.user, is_read=False,
    ).count()
    return Response({
        'success': True,
        'data': {'count': count},
    })
