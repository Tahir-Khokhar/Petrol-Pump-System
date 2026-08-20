from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class IsPumpManagerOrAbove(BasePermission):
    """Allows access only to SUPER_ADMIN and PUMP_MANAGER roles."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.Role.SUPER_ADMIN, User.Role.PUMP_MANAGER)
        )
