import uuid

from django.db import models


class Purchase(models.Model):
    """Represents a purchase from a supplier."""

    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PARTIAL = 'PARTIAL', 'Partial'
        COMPLETED = 'COMPLETED', 'Completed'

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    purchase_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='Purchase Number',
    )
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.PROTECT,
        related_name='purchases',
        verbose_name='Supplier',
    )
    fuel_type = models.ForeignKey(
        'fuel.FuelType',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='purchases',
        verbose_name='Fuel Type',
    )
    tank = models.ForeignKey(
        'fuel.Tank',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='purchases',
        verbose_name='Tank',
    )
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='purchases',
        verbose_name='Inventory Item',
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Quantity',
    )
    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Price Per Unit',
    )
    total_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='Total Cost',
    )
    purchase_date = models.DateField(verbose_name='Purchase Date')
    invoice_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Invoice Number',
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name='Payment Status',
    )
    notes = models.TextField(blank=True, verbose_name='Notes')
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_purchases',
        verbose_name='Created By',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        db_table = 'purchases'
        verbose_name = 'Purchase'
        verbose_name_plural = 'Purchases'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['supplier'], name='idx_purchase_supplier'),
            models.Index(fields=['fuel_type'], name='idx_purchase_fuel_type'),
            models.Index(fields=['tank'], name='idx_purchase_tank'),
            models.Index(fields=['purchase_date'], name='idx_purchase_date'),
            models.Index(fields=['payment_status'], name='idx_purchase_payment_status'),
        ]

    def __str__(self):
        return self.purchase_number
