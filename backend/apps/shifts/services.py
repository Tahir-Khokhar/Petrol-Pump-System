import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

logger = logging.getLogger(__name__)


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
        pass


def open_shift(employee, pump, opening_cash, user):
    """Open a new shift for an employee at a pump.

    Args:
        employee: User instance
        pump: Pump instance
        opening_cash: Decimal opening cash amount
        user: User instance performing the action

    Returns:
        The created Shift instance

    Raises:
        ValueError: if there's already an open shift for this pump
    """
    from apps.shifts.models import Shift

    # Validate no open shift exists for this pump
    existing = Shift.objects.filter(
        pump=pump,
        status=Shift.Status.OPEN,
    ).exists()
    if existing:
        raise ValueError('There is already an open shift for this pump. Close it before opening a new one.')

    shift = Shift.objects.create(
        employee=employee,
        pump=pump,
        start_time=timezone.now(),
        opening_cash=opening_cash,
        status=Shift.Status.OPEN,
    )

    _create_audit_log(
        action='CREATE',
        model_name='shifts.Shift',
        object_id=shift.uuid,
        user=user,
        changes={
            'employee': str(employee.uuid),
            'pump': str(pump.uuid),
            'opening_cash': str(opening_cash),
        },
        description=f'Shift opened for {employee.email} at {pump.pump_number}',
    )

    logger.info('Shift opened: %s at %s by %s', employee.email, pump.pump_number, user.email)

    return shift


def close_shift(shift, actual_cash, user):
    """Close a shift with cash reconciliation.

    Calculates:
        expected_cash = opening_cash + cash_sales - cash_expenses
        cash_difference = actual_cash - expected_cash

    Args:
        shift: Shift instance (must be OPEN)
        actual_cash: Decimal actual cash in drawer
        user: User instance closing the shift

    Returns:
        The updated Shift instance

    Raises:
        ValueError: if shift is not OPEN
    """
    from apps.shifts.models import Shift

    if shift.status != Shift.Status.OPEN:
        raise ValueError('Shift is not open.')

    with transaction.atomic():
        # Calculate cash sales during this shift
        from apps.sales.models import Sale
        cash_sales_result = Sale.objects.filter(
            created_at__gte=shift.start_time,
            payment_method=Sale.PaymentMethod.CASH,
            status=Sale.Status.COMPLETED,
        ).aggregate(total=Sum('total_amount'))
        cash_sales = cash_sales_result['total'] or Decimal('0')

        # Calculate cash expenses during this shift
        from apps.expenses.models import Expense
        cash_expenses_result = Expense.objects.filter(
            expense_date__gte=shift.start_time.date(),
            payment_method=Expense.PaymentMethod.CASH,
        ).aggregate(total=Sum('amount'))
        cash_expenses = cash_expenses_result['total'] or Decimal('0')

        # Calculate expected and difference
        expected_cash = shift.opening_cash + cash_sales - cash_expenses
        cash_difference = actual_cash - expected_cash

        # Count total transactions
        total_transactions = Sale.objects.filter(
            created_at__gte=shift.start_time,
            status=Sale.Status.COMPLETED,
        ).count()

        # Update shift
        shift.end_time = timezone.now()
        shift.closing_cash = actual_cash
        shift.expected_cash = expected_cash
        shift.actual_cash = actual_cash
        shift.cash_difference = cash_difference
        shift.total_sales = cash_sales
        shift.total_transactions = total_transactions
        shift.status = Shift.Status.CLOSED
        shift.save()

    _create_audit_log(
        action='UPDATE',
        model_name='shifts.Shift',
        object_id=shift.uuid,
        user=user,
        changes={
            'status': 'CLOSED',
            'cash_difference': str(cash_difference),
            'total_sales': str(cash_sales),
        },
        description=f'Shift closed for {shift.employee.email} at {shift.pump.pump_number}',
    )

    logger.info(
        'Shift closed: %s at %s, cash_diff=%s by %s',
        shift.employee.email, shift.pump.pump_number, cash_difference, user.email,
    )

    return shift


def compare_meter_with_sales(meter_reading):
    """Compare fuel_dispensed from meter reading with actual sales.

    Flags if difference > 5%.

    Args:
        meter_reading: MeterReading instance

    Returns:
        dict with 'match' (bool), 'meter_dispensed', 'actual_sales', 'difference_pct'
    """
    if meter_reading.fuel_dispensed is None:
        return {'match': None, 'meter_dispensed': None, 'actual_sales': None, 'difference_pct': None}

    from apps.sales.models import Sale

    total_sales_result = Sale.objects.filter(
        nozzle=meter_reading.nozzle,
        created_at__date=meter_reading.date,
        status=Sale.Status.COMPLETED,
    ).aggregate(total=Sum('quantity'))
    total_sales = total_sales_result['total'] or Decimal('0')

    meter_dispensed = meter_reading.fuel_dispensed

    if total_sales == Decimal('0'):
        if meter_dispensed == Decimal('0'):
            return {'match': True, 'meter_dispensed': str(meter_dispensed), 'actual_sales': '0.00', 'difference_pct': '0.00'}
        return {'match': False, 'meter_dispensed': str(meter_dispensed), 'actual_sales': '0.00', 'difference_pct': '100.00'}

    difference_pct = abs(meter_dispensed - total_sales) / total_sales * Decimal('100')
    match = difference_pct <= Decimal('5')

    return {
        'match': match,
        'meter_dispensed': str(meter_dispensed),
        'actual_sales': str(total_sales),
        'difference_pct': str(round(difference_pct, 2)),
    }
