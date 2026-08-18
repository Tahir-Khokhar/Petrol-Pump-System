import uuid

from django.db import models

from apps.customers.models.customer import Customer
from apps.fuel.models import FuelType


class Vehicle(models.Model):
    """Represents a vehicle owned by a customer."""

    class VehicleType(models.TextChoices):
        CAR = 'CAR', 'Car'
        MOTORCYCLE = 'MOTORCYCLE', 'Motorcycle'
        TRUCK = 'TRUCK', 'Truck'
        BUS = 'BUS', 'Bus'
        VAN = 'VAN', 'Van'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='vehicles',
        verbose_name='Customer',
    )
    registration_number = models.CharField(max_length=50, verbose_name='Registration Number')
    vehicle_type = models.CharField(
        max_length=20,
        choices=VehicleType.choices,
        default=VehicleType.CAR,
        verbose_name='Vehicle Type',
    )
    make = models.CharField(max_length=100, blank=True, verbose_name='Make')
    model_name = models.CharField(max_length=100, blank=True, verbose_name='Model')
    year = models.PositiveIntegerField(null=True, blank=True, verbose_name='Year')
    color = models.CharField(max_length=50, blank=True, verbose_name='Color')
    preferred_fuel_type = models.ForeignKey(
        FuelType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferred_vehicles',
        verbose_name='Preferred Fuel Type',
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
        db_table = 'vehicles'
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer'], name='idx_vehicle_customer'),
            models.Index(fields=['registration_number'], name='idx_vehicle_reg_num'),
        ]

    def __str__(self):
        return self.registration_number
