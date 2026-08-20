import uuid

from django.conf import settings
from django.db import models


class FuelPriceHistory(models.Model):
    """Tracks historical price changes for fuel types."""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    fuel_type = models.ForeignKey(
        'fuel.FuelType',
        on_delete=models.PROTECT,
        related_name='price_history',
        verbose_name='Fuel Type',
    )
    previous_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Previous Price',
    )
    new_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='New Price',
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='fuel_price_changes',
        verbose_name='Changed By',
    )
    reason = models.TextField(blank=True, default='', verbose_name='Reason for Change')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')

    class Meta:
        db_table = 'fuel_price_history'
        verbose_name = 'Fuel Price History'
        verbose_name_plural = 'Fuel Price History'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.fuel_type.name}: {self.previous_price} -> {self.new_price}'
