import uuid

from django.db import models

from apps.accounts.models import User
from apps.fuel.models import FuelType


class Pump(models.Model):
    """Represents a physical fuel pump at the petrol station."""

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        MAINTENANCE = 'MAINTENANCE', 'Maintenance'

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    pump_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Pump Number',
    )
    name = models.CharField(max_length=200, verbose_name='Pump Name')
    location = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='Location',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='Status',
    )
    assigned_employee = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_pumps',
        verbose_name='Assigned Employee',
    )
    installation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Installation Date',
    )
    last_maintenance_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Last Maintenance Date',
    )
    fuel_types = models.ManyToManyField(
        FuelType,
        through='pumps.PumpFuelType',
        related_name='pumps',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        db_table = 'pumps'
        verbose_name = 'Pump'
        verbose_name_plural = 'Pumps'
        ordering = ['pump_number']
        indexes = [
            models.Index(fields=['pump_number'], name='idx_pump_pump_number'),
            models.Index(fields=['status'], name='idx_pump_status'),
            models.Index(fields=['assigned_employee'], name='idx_pump_assigned_employee'),
        ]

    def __str__(self):
        return self.pump_number
