from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class CanManageEmployees(BasePermission):
    """Allows employee management only to SUPER_ADMIN and PUMP_MANAGER."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.Role.SUPER_ADMIN, User.Role.PUMP_MANAGER)
        )


class CanViewEmployees(BasePermission):
    """Allows employee viewing to SUPER_ADMIN, PUMP_MANAGER, ACCOUNTANT, CASHIER, PUMP_ATTENDANT."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (
                User.Role.SUPER_ADMIN,
                User.Role.PUMP_MANAGER,
                User.Role.ACCOUNTANT,
                User.Role.CASHIER,
                User.Role.PUMP_ATTENDANT,
            )
        )
