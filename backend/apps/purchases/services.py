import logging
import uuid
from datetime import datetime
from decimal import Decimal

from django.db import transaction

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


def _generate_purchase_number():
    """Generate a unique purchase number using datetime + random suffix."""
    now = datetime.now()
    date_part = now.strftime('%Y%m%d')
    random_part = uuid.uuid4().hex[:8].upper()
    return f'PUR-{date_part}-{random_part}'


@transaction.atomic
def create_purchase(validated_data, user):
    """Create a purchase with full transactional integrity.

    Args:
        validated_data: dict with supplier, fuel_type (optional), tank (optional),
                        inventory_item (optional), quantity, price_per_unit,
                        purchase_date, invoice_number, notes, payment_status
        user: User instance performing the purchase

    Returns:
        The created Purchase instance
    """
    from apps.fuel.models import FuelType, Tank
    from apps.inventory.models import InventoryItem
    from apps.purchases.models import Purchase
    from apps.suppliers.models import Supplier

    # 1. Fetch supplier
    supplier = Supplier.objects.get(uuid=validated_data['supplier'])

    # 2. Fetch optional fuel_type
    fuel_type = None
    fuel_type_uuid = validated_data.get('fuel_type')
    if fuel_type_uuid:
        fuel_type = FuelType.objects.get(uuid=fuel_type_uuid)

    # 3. Fetch optional tank
    tank = None
    tank_uuid = validated_data.get('tank')
    if tank_uuid:
        tank = Tank.objects.select_for_update().get(uuid=tank_uuid)

    # 4. Fetch optional inventory_item
    inventory_item = None
    inventory_item_uuid = validated_data.get('inventory_item')
    if inventory_item_uuid:
        inventory_item = InventoryItem.objects.get(uuid=inventory_item_uuid)

    # 5. Calculate total_cost
    quantity = validated_data['quantity']
    price_per_unit = validated_data['price_per_unit']
    total_cost = quantity * price_per_unit

    # 6. Generate purchase number
    purchase_number = _generate_purchase_number()

    # 7. Create Purchase record
    purchase = Purchase.objects.create(
        purchase_number=purchase_number,
        supplier=supplier,
        fuel_type=fuel_type,
        tank=tank,
        inventory_item=inventory_item,
        quantity=quantity,
        price_per_unit=price_per_unit,
        total_cost=total_cost,
        purchase_date=validated_data['purchase_date'],
        invoice_number=validated_data.get('invoice_number', ''),
        payment_status=validated_data.get('payment_status', Purchase.PaymentStatus.PENDING),
        notes=validated_data.get('notes', ''),
        created_by=user,
    )

    # 8. If fuel_type + tank: add quantity to tank stock
    if fuel_type and tank:
        tank.current_quantity += quantity
        tank.save(update_fields=['current_quantity', 'updated_at'])

    # 9. Audit log
    _create_audit_log(
        action='CREATE',
        model_name='purchases.Purchase',
        object_id=purchase.uuid,
        user=user,
        changes={
            'purchase_number': purchase.purchase_number,
            'supplier': str(supplier.uuid),
            'quantity': str(quantity),
            'total_cost': str(total_cost),
            'fuel_type': str(fuel_type.uuid) if fuel_type else None,
            'tank': str(tank.uuid) if tank else None,
        },
        description=f'Purchase {purchase.purchase_number} created: {quantity} units for {total_cost}',
    )

    logger.info(
        'Purchase %s created: %s units from %s by %s',
        purchase.purchase_number, quantity, supplier.company_name, user.email,
    )

    return Purchase.objects.select_related('supplier', 'fuel_type', 'tank').get(uuid=purchase.uuid)


def update_purchase_payment_status(purchase, new_status, user):
    """Update payment status of a purchase.

    Args:
        purchase: Purchase instance
        new_status: PaymentStatus enum value
        user: User instance

    Returns:
        The updated Purchase instance
    """
    old_status = purchase.payment_status
    purchase.payment_status = new_status
    purchase.save(update_fields=['payment_status', 'updated_at'])

    _create_audit_log(
        action='UPDATE',
        model_name='purchases.Purchase',
        object_id=purchase.uuid,
        user=user,
        changes={
            'payment_status': {'old': old_status, 'new': new_status},
        },
        description=f'Purchase {purchase.purchase_number} payment status changed: {old_status} -> {new_status}',
    )

    logger.info(
        'Purchase %s payment status updated: %s -> %s by %s',
        purchase.purchase_number, old_status, new_status, user.email,
    )

    return purchase
