from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class IsSuperAdmin(BasePermission):
    """Allows access only to users with SUPER_ADMIN role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.SUPER_ADMIN
        )


class IsPumpManager(BasePermission):
    """Allows access only to users with PUMP_MANAGER role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.PUMP_MANAGER
        )


class IsCashier(BasePermission):
    """Allows access only to users with CASHIER role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.CASHIER
        )


class IsPumpAttendant(BasePermission):
    """Allows access only to users with PUMP_ATTENDANT role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.PUMP_ATTENDANT
        )


class IsInventoryManager(BasePermission):
    """Allows access only to users with INVENTORY_MANAGER role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.INVENTORY_MANAGER
        )


class IsAccountant(BasePermission):
    """Allows access only to users with ACCOUNTANT role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.ACCOUNTANT
        )


class IsCustomer(BasePermission):
    """Allows access only to users with CUSTOMER role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.CUSTOMER
        )


class IsOwnerOrAdmin(BasePermission):
    """Allows access if the user is the object owner (self) or a SUPER_ADMIN."""

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # SUPER_ADMIN can access any user object
        if request.user.role == User.Role.SUPER_ADMIN:
            return True

        # Users can access their own profile
        return obj.uuid == request.user.uuid
