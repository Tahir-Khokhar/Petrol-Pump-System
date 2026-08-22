import logging
import uuid
from datetime import datetime
from decimal import Decimal

from django.db import models as django_models
from django.db import transaction
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


def _generate_receipt_number():
    """Generate a unique receipt number using datetime + random suffix."""
    now = datetime.now()
    date_part = now.strftime('%Y%m%d')
    random_part = uuid.uuid4().hex[:8].upper()
    return f'RCP-{date_part}-{random_part}'


def _generate_refund_number():
    """Generate a unique refund number using datetime + random suffix."""
    now = datetime.now()
    date_part = now.strftime('%Y%m%d')
    random_part = uuid.uuid4().hex[:8].upper()
    return f'REF-{date_part}-{random_part}'


def _get_total_refunded(sale):
    """Get total refunded amount (PENDING + APPROVED) for a sale."""
    from apps.sales.models import Refund
    result = sale.refunds.filter(
        status__in=[Refund.Status.PENDING, Refund.Status.APPROVED]
    ).aggregate(total=django_models.Sum('amount'))['total']
    return result or Decimal('0')


def _get_total_approved_refunded(sale):
    """Get total APPROVED refunded amount for a sale."""
    from apps.sales.models import Refund
    result = sale.refunds.filter(
        status=Refund.Status.APPROVED
    ).aggregate(total=django_models.Sum('amount'))['total']
    return result or Decimal('0')


@transaction.atomic
def create_sale(validated_data, user):
    """Create a sale with full transactional integrity.

    This is the CRITICAL service that orchestrates:
    1. Validates pump, nozzle, fuel_type, customer
    2. Finds and locks the tank for stock deduction
    3. Calculates all financial totals server-side
    4. Creates Sale, Payment records
    5. Updates tank stock and nozzle meter
    6. Handles corporate customer balance

    Args:
        validated_data: dict with pump (UUID str), nozzle (UUID str),
                        fuel_type (UUID str or None), quantity (Decimal),
                        discount (Decimal), payment_method (str),
                        customer (UUID str or None), notes (str)
        user: User instance performing the sale

    Returns:
        The created Sale instance (fully populated with select_related)
    """
    from apps.customers.models import Customer
    from apps.fuel.models import FuelType, Tank
    from apps.pumps.models import Nozzle, Pump
    from apps.sales.models import Sale

    # 1. Fetch and validate pump
    pump_uuid = validated_data['pump']
    pump = Pump.objects.get(uuid=pump_uuid)
    if pump.status != Pump.Status.ACTIVE:
        raise ValueError('Pump is not active.')

    # 2. Fetch and validate nozzle (must belong to pump)
    nozzle_uuid = validated_data['nozzle']
    nozzle = Nozzle.objects.select_related('fuel_type', 'pump').get(uuid=nozzle_uuid)
    if nozzle.status != Nozzle.Status.ACTIVE:
        raise ValueError('Nozzle is not active.')
    if nozzle.pump.uuid != pump.uuid:
        raise ValueError('Nozzle does not belong to the specified pump.')

    # 3. Determine fuel_type (from nozzle if not provided)
    fuel_type_uuid = validated_data.get('fuel_type')
    if fuel_type_uuid:
        fuel_type = FuelType.objects.get(uuid=fuel_type_uuid)
    else:
        fuel_type = nozzle.fuel_type

    # 4. Get price from fuel_type.current_price
    price_per_unit = fuel_type.current_price

    # 5. Validate quantity
    quantity = validated_data['quantity']
    if quantity <= Decimal('0'):
        raise ValueError('Quantity must be greater than zero.')

    # 6. Find and lock the tank for this fuel_type (active tank with stock)
    tank = Tank.objects.select_for_update().filter(
        fuel_type=fuel_type,
        status=Tank.Status.ACTIVE,
    ).order_by('-current_quantity').first()

    if tank is None:
        raise ValueError(f'No active tank found for fuel type: {fuel_type.name}')

    # 7. Validate tank has enough stock
    if tank.current_quantity < quantity:
        raise ValueError(
            f'Insufficient stock. Available: {tank.current_quantity} {fuel_type.unit}, '
            f'Requested: {quantity} {fuel_type.unit}'
        )

    # 8. Calculate totals server-side
    discount = validated_data.get('discount', Decimal('0'))
    subtotal = quantity * price_per_unit
    tax_rate = Decimal('0')  # Default tax rate
    tax_amount = subtotal * tax_rate
    total_amount = subtotal + tax_amount - discount

    # 9. Generate unique receipt number
    receipt_number = _generate_receipt_number()

    # 10. Handle optional customer
    customer = None
    customer_uuid = validated_data.get('customer')
    if customer_uuid:
        customer = Customer.objects.get(uuid=customer_uuid)

    # 11. Create Sale record
    sale = Sale.objects.create(
        receipt_number=receipt_number,
        customer=customer,
        employee=user,
        pump=pump,
        nozzle=nozzle,
        fuel_type=fuel_type,
        quantity=quantity,
        price_per_unit=price_per_unit,
        subtotal=subtotal,
        discount=discount,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        total_amount=total_amount,
        payment_method=validated_data.get('payment_method', Sale.PaymentMethod.CASH),
        status=Sale.Status.COMPLETED,
        notes=validated_data.get('notes', ''),
    )

    # 12. Reduce tank stock
    tank.current_quantity -= quantity
    tank.save(update_fields=['current_quantity', 'updated_at'])

    # 13. Update nozzle meter reading
    nozzle.current_meter_reading += quantity
    nozzle.save(update_fields=['current_meter_reading', 'updated_at'])

    # 14. Create Payment record
    try:
        from apps.payments.models import Payment
        Payment.objects.create(
            payment_reference=f'PAY-{receipt_number}',
            sale=sale,
            amount=total_amount,
            payment_method=sale.payment_method,
            status=Payment.Status.COMPLETED,
            processed_by=user,
        )
    except Exception:
        # payments app model might not be available yet
        pass

    # 15. If corporate customer, increase outstanding_balance
    if customer and customer.is_corporate:
        customer.outstanding_balance += total_amount
        customer.save(update_fields=['outstanding_balance', 'updated_at'])

    # 16. Create audit log
    _create_audit_log(
        action='CREATE',
        model_name='sales.Sale',
        object_id=sale.uuid,
        user=user,
        changes={
            'receipt_number': sale.receipt_number,
            'quantity': str(quantity),
            'total_amount': str(total_amount),
            'pump': str(pump.uuid),
            'nozzle': str(nozzle.uuid),
            'fuel_type': str(fuel_type.uuid),
        },
        description=f'Sale {sale.receipt_number} created: {quantity} units of {fuel_type.name} for {total_amount}',
    )

    logger.info(
        'Sale %s created: %s %s of %s by %s',
        sale.receipt_number, quantity, fuel_type.unit, fuel_type.name, user.email,
    )

    # 17. Return the sale with related data
    return Sale.objects.select_related(
        'customer', 'employee', 'pump', 'nozzle', 'fuel_type'
    ).get(uuid=sale.uuid)


@transaction.atomic
def process_refund(refund_data, user):
    """Process a refund for a sale.

    Args:
        refund_data: dict with sale (Sale instance), amount (Decimal),
                      reason (str)
        user: User instance processing the refund

    Returns:
        The created Refund instance
    """
    from apps.accounts.models import User
    from apps.sales.models import Refund

    sale = refund_data['sale']
    amount = refund_data['amount']
    reason = refund_data['reason']

    # 1. Validate amount <= remaining refundable
    total_refunded = _get_total_refunded(sale)
    remaining = sale.total_amount - total_refunded
    if amount > remaining:
        raise ValueError(
            f'Refund amount exceeds remaining refundable amount. Remaining: {remaining}'
        )

    # 2. Generate refund number
    refund_number = _generate_refund_number()

    # 3. Determine initial status — auto-approve for SUPER_ADMIN
    if user.role == User.Role.SUPER_ADMIN:
        refund_status = Refund.Status.APPROVED
        processed_at = timezone.now()
    else:
        refund_status = Refund.Status.PENDING
        processed_at = None

    # 4. Create Refund
    refund = Refund.objects.create(
        refund_number=refund_number,
        sale=sale,
        amount=amount,
        reason=reason,
        processed_by=user,
        status=refund_status,
        processed_at=processed_at,
    )

    # 5. If auto-approved, perform side effects
    if refund_status == Refund.Status.APPROVED:
        _apply_refund_effects(sale, refund, user)

    # 6. Audit log
    _create_audit_log(
        action='CREATE',
        model_name='sales.Refund',
        object_id=refund.uuid,
        user=user,
        changes={
            'refund_number': refund.refund_number,
            'sale': str(sale.uuid),
            'amount': str(amount),
            'status': refund_status,
        },
        description=f'Refund {refund.refund_number} created for sale {sale.receipt_number}: {amount}',
    )

    logger.info(
        'Refund %s created for sale %s: amount=%s, status=%s by %s',
        refund.refund_number, sale.receipt_number, amount, refund_status, user.email,
    )

    return refund


def _apply_refund_effects(sale, refund, user):
    """Apply side effects of an approved refund.

    - Update sale status to REFUNDED if fully refunded
    - Reverse customer balance if corporate
    - Try to add stock back to tank
    - Update payment status
    """
    from apps.sales.models import Refund, Sale as SaleModel

    # Check if fully refunded
    total_approved = _get_total_approved_refunded(sale)

    if total_approved >= sale.total_amount:
        sale.status = SaleModel.Status.REFUNDED
        sale.save(update_fields=['status'])

    # Reverse customer balance if corporate
    if sale.customer and sale.customer.is_corporate:
        sale.customer.outstanding_balance = max(
            Decimal('0'),
            sale.customer.outstanding_balance - refund.amount,
        )
        sale.customer.save(update_fields=['outstanding_balance', 'updated_at'])

    # Try to add stock back to tank
    try:
        from apps.fuel.models import Tank
        tank = Tank.objects.select_for_update().filter(
            fuel_type=sale.fuel_type,
            status=Tank.Status.ACTIVE,
        ).first()
        if tank:
            new_qty = tank.current_quantity + sale.quantity
            if new_qty <= tank.capacity:
                tank.current_quantity = new_qty
                tank.save(update_fields=['current_quantity', 'updated_at'])
    except Exception:
        pass

    # Update payment status
    try:
        from apps.payments.models import Payment
        payment = sale.payments.filter(status=Payment.Status.COMPLETED).first()
        if payment:
            payment.status = Payment.Status.REFUNDED
            payment.save(update_fields=['status', 'updated_at'])
    except Exception:
        pass
