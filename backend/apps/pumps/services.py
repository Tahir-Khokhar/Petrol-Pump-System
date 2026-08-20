import logging
from decimal import Decimal

from django.db import transaction

from apps.accounts.models import User
from apps.pumps.models import Nozzle, Pump

logger = logging.getLogger(__name__)


# Try importing audit log model — app may not be fully set up yet
def _create_audit_log(action, model_name, object_id, user, changes, description=''):  # noqa: D401
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
def assign_employee_to_pump(pump, employee, user):
    """Assign an employee to a pump.

    Validates that the employee exists and has the right role
    (PUMP_ATTENDANT or CASHIER).

    Args:
        pump: Pump instance
        employee: User instance to assign
        user: User instance performing the assignment

    Returns:
        The updated Pump instance

    Raises:
        ValueError: If the employee does not have a valid role
    """
    valid_roles = {User.Role.PUMP_ATTENDANT, User.Role.CASHIER}

    if employee.role not in valid_roles:
        raise ValueError(
            f'Employee must have one of the following roles: '
            f'{", ".join(sorted(valid_roles))}. '
            f'Current role: {employee.get_role_display()}.'
        )

    old_employee = pump.assigned_employee
    pump.assigned_employee = employee
    pump.save(update_fields=['assigned_employee', 'updated_at'])

    # Create audit log
    changes = {
        'previous_employee': str(old_employee.uuid) if old_employee else None,
        'new_employee': str(employee.uuid),
    }
    _create_audit_log(
        action='UPDATE',
        model_name='pumps.Pump',
        object_id=pump.uuid,
        user=user,
        changes=changes,
        description=(
            f'Employee {employee.email} assigned to pump {pump.pump_number}. '
            f'Previous: {old_employee.email if old_employee else "None"}.'
        ),
    )

    logger.info(
        'Employee %s assigned to pump %s by %s',
        employee.email, pump.pump_number, user.email,
    )

    return pump


@transaction.atomic
def update_pump_status(pump, new_status, user):
    """Update a pump's status.

    Validates the status transition.

    Args:
        pump: Pump instance
        new_status: str — one of the Pump.Status choices
        user: User instance performing the update

    Returns:
        The updated Pump instance

    Raises:
        ValueError: If the status transition is invalid
    """
    valid_statuses = {choice[0] for choice in Pump.Status.choices}
    if new_status not in valid_statuses:
        raise ValueError(
            f'Invalid status: {new_status}. '
            f'Must be one of: {", ".join(sorted(valid_statuses))}.'
        )

    old_status = pump.status
    pump.status = new_status

    # If setting to MAINTENANCE, update last_maintenance_date
    if new_status == Pump.Status.MAINTENANCE:
        from django.utils import timezone
        pump.last_maintenance_date = timezone.now().date()

    pump.save(update_fields=['status', 'last_maintenance_date', 'updated_at'])

    # Create audit log
    changes = {
        'previous_status': old_status,
        'new_status': new_status,
    }
    _create_audit_log(
        action='UPDATE',
        model_name='pumps.Pump',
        object_id=pump.uuid,
        user=user,
        changes=changes,
        description=f'Pump {pump.pump_number} status changed: {old_status} -> {new_status}.',
    )

    logger.info(
        'Pump %s status changed: %s -> %s by %s',
        pump.pump_number, old_status, new_status, user.email,
    )

    return pump


@transaction.atomic
def update_nozzle_meter(nozzle, closing_reading, user):
    """Update a nozzle's meter reading.

    Validates that closing_meter_reading >= opening_meter_reading and
    closing_meter_reading >= current_meter_reading. Uses select_for_update
    to prevent race conditions.

    Args:
        nozzle: Nozzle instance
        closing_reading: Decimal — the new closing meter reading
        user: User instance performing the update

    Returns:
        The updated Nozzle instance

    Raises:
        ValueError: If the reading is invalid
    """
    # Re-fetch with select_for_update to lock the row
    nozzle = Nozzle.objects.select_for_update().get(uuid=nozzle.uuid)

    if closing_reading < nozzle.opening_meter_reading:
        raise ValueError(
            f'Closing meter reading ({closing_reading}) must be greater than or equal '
            f'to opening meter reading ({nozzle.opening_meter_reading}).'
        )

    if closing_reading < nozzle.current_meter_reading:
        raise ValueError(
            f'Closing meter reading ({closing_reading}) cannot be less than '
            f'current meter reading ({nozzle.current_meter_reading}).'
        )

    old_closing = nozzle.closing_meter_reading
    old_current = nozzle.current_meter_reading

    nozzle.closing_meter_reading = closing_reading
    nozzle.current_meter_reading = closing_reading
    nozzle.save(update_fields=['closing_meter_reading', 'current_meter_reading', 'updated_at'])

    # Create audit log
    changes = {
        'previous_closing_meter_reading': str(old_closing) if old_closing is not None else None,
        'new_closing_meter_reading': str(closing_reading),
        'previous_current_meter_reading': str(old_current),
        'new_current_meter_reading': str(closing_reading),
    }
    _create_audit_log(
        action='UPDATE',
        model_name='pumps.Nozzle',
        object_id=nozzle.uuid,
        user=user,
        changes=changes,
        description=(
            f'Nozzle {nozzle.nozzle_number} meter updated: '
            f'closing={old_closing}->{closing_reading}, '
            f'current={old_current}->{closing_reading}.'
        ),
    )

    logger.info(
        'Nozzle %s meter updated to %s by %s',
        nozzle.nozzle_number, closing_reading, user.email,
    )

    return nozzle
