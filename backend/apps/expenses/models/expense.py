import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Expense(models.Model):
    """Represents an expense at the petrol pump."""

    class Category(models.TextChoices):
        ELECTRICITY = 'ELECTRICITY', 'Electricity'
        SALARIES = 'SALARIES', 'Salaries'
        MAINTENANCE = 'MAINTENANCE', 'Maintenance'
        RENT = 'RENT', 'Rent'
        SECURITY = 'SECURITY', 'Security'
        CLEANING = 'CLEANING', 'Cleaning'
        EQUIPMENT = 'EQUIPMENT', 'Equipment'
        FUEL = 'FUEL', 'Fuel'
        OTHER = 'OTHER', 'Other'

    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        CARD = 'CARD', 'Card'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
        OTHER = 'OTHER', 'Other'

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
        verbose_name='Category',
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Amount',
    )
    description = models.TextField(verbose_name='Description')
    employee = models.ForeignKey(
        'accounts.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='expenses',
        verbose_name='Employee',
    )
    expense_date = models.DateField(verbose_name='Expense Date')
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name='Payment Method',
    )
    receipt_reference = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='Receipt Reference',
    )
    notes = models.TextField(blank=True, verbose_name='Notes')
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_expenses',
        verbose_name='Created By',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        db_table = 'expenses'
        verbose_name = 'Expense'
        verbose_name_plural = 'Expenses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category'], name='idx_expense_category'),
            models.Index(fields=['expense_date'], name='idx_expense_date'),
            models.Index(fields=['payment_method'], name='idx_expense_payment_method'),
            models.Index(fields=['created_by'], name='idx_expense_created_by'),
        ]

    def __str__(self):
        return f'{self.get_category_display()} - {self.amount}'
