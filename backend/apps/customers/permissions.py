from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class IsCustomerOwner(BasePermission):
    """Checks if request.user.customer_profile matches the customer object."""

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            return getattr(request.user, 'customer_profile', None) is not None and request.user.customer_profile.uuid == obj.uuid
        except AttributeError:
            return False


class CanManageCustomers(BasePermission):
    """Allows access only to SUPER_ADMIN and PUMP_MANAGER roles."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.Role.SUPER_ADMIN, User.Role.PUMP_MANAGER)
        )
