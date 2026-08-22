import uuid

from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import User


class Refund(models.Model):
    """Represents a refund for a sale."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    refund_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Refund Number',
    )
    sale = models.ForeignKey(
        'sales.Sale',
        on_delete=models.PROTECT,
        related_name='refunds',
        verbose_name='Sale',
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Refund Amount',
    )
    reason = models.TextField(verbose_name='Reason')
    processed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='processed_refunds',
        verbose_name='Processed By',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Status',
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Created At',
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Processed At',
    )

    class Meta:
        db_table = 'refunds'
        verbose_name = 'Refund'
        verbose_name_plural = 'Refunds'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name='chk_refund_amount_positive',
            )
        ]
        indexes = [
            models.Index(fields=['sale'], name='idx_refund_sale'),
            models.Index(fields=['processed_by'], name='idx_refund_processed_by'),
            models.Index(fields=['status'], name='idx_refund_status'),
        ]

    def __str__(self):
        return self.refund_number
