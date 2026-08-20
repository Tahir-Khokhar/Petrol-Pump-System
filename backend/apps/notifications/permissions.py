from rest_framework.permissions import BasePermission


class IsNotificationOwner(BasePermission):
    """Check that the notification belongs to the requesting user."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
