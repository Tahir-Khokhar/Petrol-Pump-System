import uuid

from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator


class Tank(models.Model):
    """Represents a fuel storage tank at the petrol pump."""

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        MAINTENANCE = 'MAINTENANCE', 'Maintenance'

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    tank_number = models.CharField(max_length=20, unique=True, verbose_name='Tank Number')
    fuel_type = models.ForeignKey(
        'fuel.FuelType',
        on_delete=models.PROTECT,
        related_name='tanks',
        verbose_name='Fuel Type',
    )
    capacity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Capacity',
    )
    current_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Current Quantity',
    )
    minimum_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Minimum Quantity',
    )
    location = models.CharField(max_length=200, blank=True, default='', verbose_name='Location')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='Status',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        db_table = 'tanks'
        verbose_name = 'Tank'
        verbose_name_plural = 'Tanks'
        ordering = ['tank_number']
        constraints = [
            models.CheckConstraint(
                condition=Q(current_quantity__gte=0) & Q(current_quantity__lte=models.F('capacity')),
                name='chk_tank_quantity_within_capacity',
            )
        ]
        indexes = [
            models.Index(fields=['fuel_type'], name='idx_tank_fuel_type'),
            models.Index(fields=['status'], name='idx_tank_status'),
            models.Index(fields=['tank_number'], name='idx_tank_number'),
        ]

    def __str__(self):
        return self.tank_number
