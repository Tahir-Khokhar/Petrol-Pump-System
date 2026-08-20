import uuid

from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import User


class Payment(models.Model):
    """Represents a payment for a sale."""

    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        CARD = 'CARD', 'Card'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
        DIGITAL_WALLET = 'DIGITAL_WALLET', 'Digital Wallet'
        CREDIT = 'CREDIT', 'Credit'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    payment_reference = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name='Payment Reference',
    )
    sale = models.ForeignKey(
        'sales.Sale',
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name='Sale',
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Amount',
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        verbose_name='Payment Method',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Status',
    )
    transaction_ref = models.CharField(
        max_length=200, blank=True, verbose_name='Transaction Reference')
    processed_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name='processed_payments',
        verbose_name='Processed By',
    )
    notes = models.TextField(blank=True, verbose_name='Notes')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gte=0),
                name='chk_payment_amount_non_negative',
            )
        ]
        indexes = [
            models.Index(fields=['sale'], name='idx_payment_sale'),
            models.Index(fields=['status'], name='idx_payment_status'),
            models.Index(fields=['payment_method'], name='idx_payment_method'),
            models.Index(fields=['created_at'], name='idx_payment_created_at'),
        ]

    def __str__(self):
        return self.payment_reference
