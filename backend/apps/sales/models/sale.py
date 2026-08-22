import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.accounts.models import User
from apps.customers.models import Customer
from apps.fuel.models import FuelType
from apps.pumps.models import Nozzle, Pump


class Sale(models.Model):
    """Represents a fuel sale transaction."""

    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        CARD = 'CARD', 'Card'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
        DIGITAL_WALLET = 'DIGITAL_WALLET', 'Digital Wallet'
        CREDIT = 'CREDIT', 'Credit'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUNDED = 'REFUNDED', 'Refunded'

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='Receipt Number',
    )
    customer = models.ForeignKey(
        Customer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sales',
        verbose_name='Customer',
    )
    employee = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='sales',
        verbose_name='Employee',
    )
    pump = models.ForeignKey(
        Pump,
        on_delete=models.PROTECT,
        related_name='sales',
        verbose_name='Pump',
    )
    nozzle = models.ForeignKey(
        Nozzle,
        on_delete=models.PROTECT,
        related_name='sales',
        verbose_name='Nozzle',
    )
    fuel_type = models.ForeignKey(
        FuelType,
        on_delete=models.PROTECT,
        related_name='sales',
        verbose_name='Fuel Type',
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Quantity',
    )
    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Price Per Unit',
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Subtotal',
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Discount',
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0,
        verbose_name='Tax Rate',
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Tax Amount',
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Total Amount',
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name='Payment Method',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.COMPLETED,
        verbose_name='Status',
    )
    notes = models.TextField(blank=True, verbose_name='Notes')
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Created At',
    )

    class Meta:
        db_table = 'sales'
        verbose_name = 'Sale'
        verbose_name_plural = 'Sales'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['receipt_number'], name='idx_sale_receipt_number'),
            models.Index(fields=['customer'], name='idx_sale_customer'),
            models.Index(fields=['employee'], name='idx_sale_employee'),
            models.Index(fields=['pump'], name='idx_sale_pump'),
            models.Index(fields=['fuel_type'], name='idx_sale_fuel_type'),
            models.Index(fields=['payment_method'], name='idx_sale_payment_method'),
            models.Index(fields=['status'], name='idx_sale_status'),
            models.Index(fields=['created_at'], name='idx_sale_created_at'),
        ]

    def __str__(self):
        return self.receipt_number

    def calculate_totals(self):
        """Calculate subtotal, tax_amount, and total_amount."""
        self.subtotal = self.quantity * self.price_per_unit
        self.tax_amount = self.subtotal * self.tax_rate
        self.total_amount = self.subtotal + self.tax_amount - self.discount
