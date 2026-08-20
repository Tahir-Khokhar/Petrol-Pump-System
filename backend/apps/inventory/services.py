import logging
from decimal import Decimal

from django.db import models as django_models, transaction

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


@transaction.atomic
def adjust_stock(inventory_item, quantity, transaction_type, user, notes='', reference=''):
    """Adjust stock for an inventory item with transactional integrity.

    Args:
        inventory_item: InventoryItem instance (will be locked via select_for_update)
        quantity: Decimal, must be > 0
        transaction_type: TransactionType enum value
        user: User instance performing the action
        notes: Optional notes
        reference: Optional reference string

    Returns:
        The created InventoryTransaction instance

    Raises:
        ValueError: if stock would go negative for STOCK_OUT/ADJUSTMENT/DAMAGED
    """
    from apps.inventory.models import InventoryItem, InventoryTransaction

    # Lock the item row for concurrent safety
    item = InventoryItem.objects.select_for_update().get(uuid=inventory_item.uuid)
    previous_stock = item.current_stock

    # For outgoing transactions, validate stock won't go negative
    if transaction_type in [
        InventoryTransaction.TransactionType.STOCK_OUT,
        InventoryTransaction.TransactionType.ADJUSTMENT,
        InventoryTransaction.TransactionType.DAMAGED,
    ]:
        if previous_stock < quantity:
            raise ValueError(
                f'Insufficient stock. Current: {previous_stock}, Requested: {quantity}'
            )
        new_stock = previous_stock - quantity
    else:
        # STOCK_IN, RETURN — add to stock
        new_stock = previous_stock + quantity

    # Create the transaction record
    txn = InventoryTransaction.objects.create(
        inventory_item=item,
        transaction_type=transaction_type,
        quantity=quantity,
        previous_stock=previous_stock,
        new_stock=new_stock,
        reference=reference,
        notes=notes,
        performed_by=user,
    )

    # Update the item stock
    item.current_stock = new_stock
    item.save(update_fields=['current_stock', 'updated_at'])

    # Audit log
    _create_audit_log(
        action='UPDATE',
        model_name='inventory.InventoryItem',
        object_id=item.uuid,
        user=user,
        changes={
            'transaction_type': transaction_type,
            'quantity': str(quantity),
            'previous_stock': str(previous_stock),
            'new_stock': str(new_stock),
        },
        description=f'Stock {transaction_type}: {quantity} for {item.name} (SKU: {item.sku})',
    )

    logger.info(
        'Stock adjustment: %s %s of %s by %s',
        transaction_type, quantity, item.sku, user.email,
    )

    return txn


def check_low_stock():
    """Return queryset of inventory items where current_stock <= minimum_stock_level."""
    from apps.inventory.models import InventoryItem
    return InventoryItem.objects.filter(
        is_active=True,
        current_stock__lte=django_models.F('minimum_stock_level'),
    )
