import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import F, Q

from apps.fuel.models import FuelType, FuelPriceHistory, Tank

logger = logging.getLogger(__name__)


# Try importing audit log model — app may not be fully set up yet
def _create_audit_log(action, model_name, object_id, user, changes, description=''):
    """Create an audit log entry if the audit_logs app is available."""
    try:
        from apps.audit_logs.models import AuditLog
        AuditLog.objects.create(
            action=action,
            model_name=model_name,
            object_id=str(object_id),
            performed_by=user,
            changes=changes,
            description=description,
        )
    except Exception:
        # audit_logs app or model not available — skip silently
        pass


@transaction.atomic
def update_fuel_price(fuel_type, new_price, changed_by_user, reason=''):
    """Update a fuel type's price, creating a history record.

    Args:
        fuel_type: FuelType instance
        new_price: Decimal — the new price to set
        changed_by_user: User instance performing the change
        reason: Optional text reason for the change

    Returns:
        The updated FuelType instance
    """
    previous_price = fuel_type.current_price

    # Create price history record
    FuelPriceHistory.objects.create(
        fuel_type=fuel_type,
        previous_price=previous_price,
        new_price=new_price,
        changed_by=changed_by_user,
        reason=reason,
    )

    # Update the fuel type's current price
    fuel_type.current_price = new_price
    fuel_type.save(update_fields=['current_price', 'updated_at'])

    # Create audit log
    changes = {
        'previous_price': str(previous_price),
        'new_price': str(new_price),
    }
    _create_audit_log(
        action='UPDATE',
        model_name='fuel.FuelType',
        object_id=fuel_type.uuid,
        user=changed_by_user,
        changes=changes,
        description=f'Fuel price changed: {previous_price} -> {new_price}. Reason: {reason}',
    )

    logger.info(
        'Fuel price updated for %s: %s -> %s by %s',
        fuel_type.name, previous_price, new_price, changed_by_user.email,
    )

    return fuel_type


@transaction.atomic
def adjust_tank_stock(tank, adjustment_quantity, user, reason=''):
    """Adjust a tank's current stock level.

    Uses select_for_update to prevent race conditions.

    Args:
        tank: Tank instance (will be re-fetched with select_for_update)
        adjustment_quantity: Decimal — positive to add, negative to remove
        user: User instance performing the adjustment
        reason: Optional text reason for the adjustment

    Returns:
        The updated Tank instance
    """
    # Re-fetch with select_for_update to lock the row
    tank = Tank.objects.select_for_update().get(uuid=tank.uuid)

    new_quantity = tank.current_quantity + adjustment_quantity

    # Validate constraints
    if new_quantity < 0:
        raise ValueError(
            f'Adjustment would result in negative stock. '
            f'Current: {tank.current_quantity}, Adjustment: {adjustment_quantity}'
        )

    if new_quantity > tank.capacity:
        raise ValueError(
            f'Adjustment would exceed tank capacity. '
            f'Capacity: {tank.capacity}, Current: {tank.current_quantity}, '
            f'Adjustment: {adjustment_quantity}'
        )

    old_quantity = tank.current_quantity
    tank.current_quantity = new_quantity
    tank.save(update_fields=['current_quantity', 'updated_at'])

    # Create audit log
    changes = {
        'previous_quantity': str(old_quantity),
        'new_quantity': str(new_quantity),
        'adjustment': str(adjustment_quantity),
    }
    _create_audit_log(
        action='UPDATE',
        model_name='fuel.Tank',
        object_id=tank.uuid,
        user=user,
        changes=changes,
        description=(
            f'Tank {tank.tank_number} stock adjusted by {adjustment_quantity}. '
            f'Reason: {reason}'
        ),
    )

    logger.info(
        'Tank %s stock adjusted: %s -> %s (%+s) by %s',
        tank.tank_number, old_quantity, new_quantity, adjustment_quantity, user.email,
    )

    return tank
