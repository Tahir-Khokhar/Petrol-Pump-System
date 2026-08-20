import uuid

from django.db import models
from django.db.models import Q


class InventoryItem(models.Model):
    """Represents an inventory item at the petrol pump."""

    class Category(models.TextChoices):
        FUEL = 'FUEL', 'Fuel'
        LUBRICANT = 'LUBRICANT', 'Lubricant'
        ENGINE_OIL = 'ENGINE_OIL', 'Engine Oil'
        COOLANT = 'COOLANT', 'Coolant'
        CAR_ACCESSORY = 'CAR_ACCESSORY', 'Car Accessory'
        OTHER = 'OTHER', 'Other'

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(max_length=200, verbose_name='Name')
    sku = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='SKU',
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
        verbose_name='Category',
    )
    description = models.TextField(blank=True, verbose_name='Description')
    unit = models.CharField(max_length=20, default='Piece', verbose_name='Unit')
    current_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Current Stock',
    )
    minimum_stock_level = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Minimum Stock Level',
    )
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Cost Price',
    )
    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Selling Price',
    )
    is_active = models.BooleanField(default=True, verbose_name='Is Active')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        db_table = 'inventory_items'
        verbose_name = 'Inventory Item'
        verbose_name_plural = 'Inventory Items'
        ordering = ['name']
        constraints = [
            models.CheckConstraint(
                condition=Q(current_stock__gte=0),
                name='chk_inventory_item_stock_non_negative',
            ),
        ]
        indexes = [
            models.Index(fields=['sku'], name='idx_inventory_item_sku'),
            models.Index(fields=['category'], name='idx_inventory_item_category'),
            models.Index(fields=['is_active'], name='idx_inventory_item_is_active'),
        ]

    @property
    def is_low_stock(self):
        return self.current_stock <= self.minimum_stock_level

    def __str__(self):
        return self.name
