from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class CanManageExpenses(BasePermission):
    """Allows SUPER_ADMIN, PUMP_MANAGER, ACCOUNTANT."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in [
                User.Role.SUPER_ADMIN,
                User.Role.PUMP_MANAGER,
                User.Role.ACCOUNTANT,
            ]
        )
