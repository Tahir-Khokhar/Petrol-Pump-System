from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class CanCreateSale(BasePermission):
    """Allows CASHIER, PUMP_MANAGER, SUPER_ADMIN to create sales."""

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


class CanViewAllSales(BasePermission):
    """Allows SUPER_ADMIN, PUMP_MANAGER, ACCOUNTANT to view all sales."""

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


class CanProcessRefund(BasePermission):
    """Allows SUPER_ADMIN, PUMP_MANAGER to process refunds."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in [
                User.Role.SUPER_ADMIN,
                User.Role.PUMP_MANAGER,
            ]
        )


class IsSaleOwnerOrAdmin(BasePermission):
    """Allows a customer to view their own sales, or admins to view any."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role in [User.Role.SUPER_ADMIN, User.Role.PUMP_MANAGER, User.Role.ACCOUNTANT]:
            return True
        # Customer can view their own sales
        if user.role == User.Role.CUSTOMER:
            try:
                return obj.customer and obj.customer.user and obj.customer.user.uuid == user.uuid
            except Exception:
                return False
        # Cashier can view their own sales
        if user.role == User.Role.CASHIER:
            return obj.employee.uuid == user.uuid
        return False
