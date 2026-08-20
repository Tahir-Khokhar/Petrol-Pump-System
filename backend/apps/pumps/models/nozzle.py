import uuid

from django.db import models
from django.db.models import Q

from apps.fuel.models import FuelType


class Nozzle(models.Model):
    """Represents a nozzle attached to a pump."""

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        MAINTENANCE = 'MAINTENANCE', 'Maintenance'

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    nozzle_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Nozzle Number',
    )
    pump = models.ForeignKey(
        'pumps.Pump',
        on_delete=models.PROTECT,
        related_name='nozzles',
        verbose_name='Pump',
    )
    fuel_type = models.ForeignKey(
        FuelType,
        on_delete=models.PROTECT,
        related_name='nozzles',
        verbose_name='Fuel Type',
    )
    opening_meter_reading = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Opening Meter Reading',
    )
    closing_meter_reading = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Closing Meter Reading',
    )
    current_meter_reading = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Current Meter Reading',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='Status',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        db_table = 'nozzles'
        verbose_name = 'Nozzle'
        verbose_name_plural = 'Nozzles'
        ordering = ['nozzle_number']
        constraints = [
            models.CheckConstraint(
                condition=Q(closing_meter_reading__isnull=True) | Q(closing_meter_reading__gte=models.F('opening_meter_reading')),
                name='chk_closing_gte_opening',
            ),
            models.CheckConstraint(
                condition=models.Q(current_meter_reading__gte=models.F('opening_meter_reading')),
                name='chk_current_gte_opening',
            ),
        ]
        indexes = [
            models.Index(fields=['pump'], name='idx_nozzle_pump'),
            models.Index(fields=['fuel_type'], name='idx_nozzle_fuel_type'),
            models.Index(fields=['status'], name='idx_nozzle_status'),
            models.Index(fields=['nozzle_number'], name='idx_nozzle_nozzle_number'),
        ]

    def __str__(self):
        return self.nozzle_number
