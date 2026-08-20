import logging

from apps.accounts.models import User
from apps.notifications.models import Notification

logger = logging.getLogger(__name__)


def create_notification(
    user,
    title,
    message,
    notification_type='GENERAL',
    related_model='',
    related_id='',
):
    """Create a notification for a user."""
    try:
        Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            related_object_model=related_model,
            related_object_id=str(related_id) if related_id else '',
        )
    except Exception:
        logger.exception('Failed to create notification for user %s', user)


def _get_staff_users():
    """Get users who should receive system alerts."""
    return User.objects.filter(
        role__in=(
            User.Role.SUPER_ADMIN,
            User.Role.PUMP_MANAGER,
            User.Role.INVENTORY_MANAGER,
        ),
        is_active=True,
    )


def notify_low_fuel_stock(fuel_type, current_stock, minimum_level):
    """Create notifications for all SUPER_ADMIN, PUMP_MANAGER, INVENTORY_MANAGER users."""
    title = f'Low Fuel Stock Alert: {fuel_type.name}'
    message = (
        f'Fuel stock for {fuel_type.name} is critically low. '
        f'Current stock: {current_stock}L, Minimum level: {minimum_level}L.'
    )
    users = _get_staff_users()
    for user in users:
        create_notification(
            user=user,
            title=title,
            message=message,
            notification_type=Notification.NotificationType.LOW_FUEL_STOCK,
            related_model='fuel.FuelType',
            related_id=str(fuel_type.uuid),
        )


def notify_low_inventory(item, current_stock, minimum_level):
    """Create notifications for low inventory items."""
    title = f'Low Inventory Alert: {item.name}'
    message = (
        f'Inventory item "{item.name}" (SKU: {item.sku}) is running low. '
        f'Current stock: {current_stock}, Minimum level: {minimum_level}.'
    )
    users = _get_staff_users()
    for user in users:
        create_notification(
            user=user,
            title=title,
            message=message,
            notification_type=Notification.NotificationType.LOW_INVENTORY,
            related_model='inventory.InventoryItem',
            related_id=str(item.uuid),
        )


def notify_meter_difference(nozzle, meter_dispensed, sales_total):
    """Flag unusual differences between meter readings and sales."""
    difference = meter_dispensed - sales_total
    title = f'Meter Difference Alert: Nozzle {nozzle.nozzle_number}'
    message = (
        f'Significant difference detected for Nozzle {nozzle.nozzle_number}. '
        f'Meter dispensed: {meter_dispensed}L, Sales total: {sales_total}L, '
        f'Difference: {difference}L.'
    )
    users = User.objects.filter(
        role__in=(User.Role.SUPER_ADMIN, User.Role.PUMP_MANAGER),
        is_active=True,
    )
    for user in users:
        create_notification(
            user=user,
            title=title,
            message=message,
            notification_type=Notification.NotificationType.METER_DIFFERENCE,
            related_model='pumps.Nozzle',
            related_id=str(nozzle.uuid),
        )
