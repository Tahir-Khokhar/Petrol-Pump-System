import uuid

from django.db import models


class Notification(models.Model):
    """Stores user notifications for alerts and system messages."""

    class NotificationType(models.TextChoices):
        LOW_FUEL_STOCK = 'LOW_FUEL_STOCK', 'Low Fuel Stock'
        LOW_INVENTORY = 'LOW_INVENTORY', 'Low Inventory'
        STOCK_ADJUSTMENT = 'STOCK_ADJUSTMENT', 'Stock Adjustment'
        FAILED_PAYMENT = 'FAILED_PAYMENT', 'Failed Payment'
        METER_DIFFERENCE = 'METER_DIFFERENCE', 'Meter Difference'
        CREDIT_LIMIT_WARNING = 'CREDIT_LIMIT_WARNING', 'Credit Limit Warning'
        SHIFT_CASH_DIFFERENCE = 'SHIFT_CASH_DIFFERENCE', 'Shift Cash Difference'
        GENERAL = 'GENERAL', 'General'

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='User',
    )
    title = models.CharField(
        max_length=300,
        verbose_name='Title',
    )
    message = models.TextField(verbose_name='Message')
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
        verbose_name='Notification Type',
    )
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Is Read',
    )
    related_object_model = models.CharField(
        max_length=100, blank=True, verbose_name='Related Object Model')
    related_object_id = models.CharField(
        max_length=100, blank=True, verbose_name='Related Object ID')
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Created At',
    )

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user'], name='idx_notification_user'),
            models.Index(fields=['is_read'], name='idx_notification_is_read'),
            models.Index(fields=['notification_type'], name='idx_notification_type'),
            models.Index(fields=['created_at'], name='idx_notification_created_at'),
        ]

    def __str__(self):
        return self.title
