import uuid

from django.db import models


class Shift(models.Model):
    """Represents a work shift for an employee at a pump."""

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        CLOSED = 'CLOSED', 'Closed'

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    employee = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='shifts',
        verbose_name='Employee',
    )
    pump = models.ForeignKey(
        'pumps.Pump',
        on_delete=models.PROTECT,
        related_name='shifts',
        verbose_name='Pump',
    )
    start_time = models.DateTimeField(verbose_name='Start Time')
    end_time = models.DateTimeField(
        null=True, blank=True, verbose_name='End Time')
    opening_cash = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Opening Cash',
    )
    closing_cash = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Closing Cash',
    )
    expected_cash = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Expected Cash',
    )
    actual_cash = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Actual Cash',
    )
    cash_difference = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Cash Difference',
    )
    total_sales = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Total Sales',
    )
    total_transactions = models.PositiveIntegerField(
        default=0,
        verbose_name='Total Transactions',
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN,
        verbose_name='Status',
    )
    notes = models.TextField(blank=True, verbose_name='Notes')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        db_table = 'shifts'
        verbose_name = 'Shift'
        verbose_name_plural = 'Shifts'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['employee'], name='idx_shift_employee'),
            models.Index(fields=['pump'], name='idx_shift_pump'),
            models.Index(fields=['status'], name='idx_shift_status'),
            models.Index(fields=['start_time'], name='idx_shift_start_time'),
        ]

    def __str__(self):
        return f'{self.employee} - {self.pump} ({self.get_status_display()})'
