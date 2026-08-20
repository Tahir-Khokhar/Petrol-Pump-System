import uuid

from django.db import models


class FuelType(models.Model):
    """Represents a type of fuel sold at the petrol pump."""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(max_length=100, unique=True, verbose_name='Fuel Name')
    code = models.CharField(max_length=20, unique=True, verbose_name='Fuel Code')
    description = models.TextField(blank=True, default='', verbose_name='Description')
    unit = models.CharField(max_length=20, default='Liter', verbose_name='Unit of Measurement')
    current_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Current Price',
    )
    minimum_stock_level = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Minimum Stock Level',
    )
    is_active = models.BooleanField(default=True, verbose_name='Is Active')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        db_table = 'fuel_types'
        verbose_name = 'Fuel Type'
        verbose_name_plural = 'Fuel Types'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'], name='idx_fuel_type_name'),
            models.Index(fields=['code'], name='idx_fuel_type_code'),
            models.Index(fields=['is_active'], name='idx_fuel_type_is_active'),
        ]

    def __str__(self):
        return self.name
