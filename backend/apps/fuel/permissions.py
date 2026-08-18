from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class IsSuperAdminOrPumpManager(BasePermission):
    """Allows access only to SUPER_ADMIN or PUMP_MANAGER."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (
                User.Role.SUPER_ADMIN,
                User.Role.PUMP_MANAGER,
            )
        )


class IsFuelManager(BasePermission):
    """Allows access only to SUPER_ADMIN, PUMP_MANAGER, or INVENTORY_MANAGER."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (
                User.Role.SUPER_ADMIN,
                User.Role.PUMP_MANAGER,
                User.Role.INVENTORY_MANAGER,
            )
        )
