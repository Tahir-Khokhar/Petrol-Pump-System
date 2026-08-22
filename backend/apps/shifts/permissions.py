from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class CanManageShifts(BasePermission):
    """Allows SUPER_ADMIN, PUMP_MANAGER."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in [
                User.Role.SUPER_ADMIN,
                User.Role.PUMP_MANAGER,
            ]
        )


class CanOpenCloseShift(BasePermission):
    """Allows CASHIER, PUMP_MANAGER, SUPER_ADMIN."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in [
                User.Role.CASHIER,
                User.Role.PUMP_MANAGER,
                User.Role.SUPER_ADMIN,
            ]
        )


class CanCreateMeterReading(BasePermission):
    """Allows SUPER_ADMIN, PUMP_MANAGER, CASHIER, PUMP_ATTENDANT."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in [
                User.Role.SUPER_ADMIN,
                User.Role.PUMP_MANAGER,
                User.Role.CASHIER,
                User.Role.PUMP_ATTENDANT,
            ]
        )
