import uuid

from django.db import models


class MeterReading(models.Model):
    """Records meter readings for nozzles during shifts."""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    shift = models.ForeignKey(
        'shifts.Shift',
        on_delete=models.PROTECT,
        related_name='meter_readings',
        verbose_name='Shift',
    )
    nozzle = models.ForeignKey(
        'pumps.Nozzle',
        on_delete=models.PROTECT,
        related_name='meter_readings',
        verbose_name='Nozzle',
    )
    opening_reading = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Opening Reading',
    )
    closing_reading = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Closing Reading',
    )
    fuel_dispensed = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Fuel Dispensed',
    )
    sales_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Sales Count',
    )
    date = models.DateField(verbose_name='Date')
    recorded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='meter_readings',
        verbose_name='Recorded By',
    )
    notes = models.TextField(blank=True, verbose_name='Notes')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')

    class Meta:
        db_table = 'meter_readings'
        verbose_name = 'Meter Reading'
        verbose_name_plural = 'Meter Readings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shift'], name='idx_meter_reading_shift'),
            models.Index(fields=['nozzle'], name='idx_meter_reading_nozzle'),
            models.Index(fields=['date'], name='idx_meter_reading_date'),
        ]

    def __str__(self):
        return f'{self.nozzle} - {self.date}'
