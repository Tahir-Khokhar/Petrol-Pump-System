import uuid

from django.db import models


__all__ = ['InventoryTransaction']

class InventoryTransaction(models.Model):
    """Records stock movements for inventory items."""

    class TransactionType(models.TextChoices):
        STOCK_IN = 'STOCK_IN', 'Stock In'
        STOCK_OUT = 'STOCK_OUT', 'Stock Out'
        ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'
        RETURN = 'RETURN', 'Return'
        DAMAGED = 'DAMAGED', 'Damaged'

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name='Inventory Item',
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        default=TransactionType.STOCK_IN,
        verbose_name='Transaction Type',
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Quantity',
    )
    previous_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Previous Stock',
    )
    new_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='New Stock',
    )
    reference = models.CharField(
        max_length=200, blank=True, verbose_name='Reference')
    notes = models.TextField(blank=True, verbose_name='Notes')
    performed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='inventory_transactions',
        verbose_name='Performed By',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')

    class Meta:
        db_table = 'inventory_transactions'
        verbose_name = 'Inventory Transaction'
        verbose_name_plural = 'Inventory Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['inventory_item'], name='idx_inv_trans_item'),
            models.Index(fields=['transaction_type'], name='idx_inv_trans_type'),
            models.Index(fields=['created_at'], name='idx_inv_trans_created'),
        ]

    def __str__(self):
        return f'{self.get_transaction_type_display()} - {self.inventory_item.name}'
