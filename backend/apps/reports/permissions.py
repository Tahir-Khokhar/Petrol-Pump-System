from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class CanViewReports(BasePermission):
    """Allows access only to SUPER_ADMIN, PUMP_MANAGER, and ACCOUNTANT roles."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (
                User.Role.SUPER_ADMIN,
                User.Role.PUMP_MANAGER,
                User.Role.ACCOUNTANT,
            )
        )


class CanViewDashboard(BasePermission):
    """Allows access to SUPER_ADMIN, PUMP_MANAGER, ACCOUNTANT, and CASHIER roles."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (
                User.Role.SUPER_ADMIN,
                User.Role.PUMP_MANAGER,
                User.Role.ACCOUNTANT,
                User.Role.CASHIER,
            )
        )
