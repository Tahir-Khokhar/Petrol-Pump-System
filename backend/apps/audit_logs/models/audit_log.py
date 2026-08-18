import uuid

from django.db import models


class AuditLog(models.Model):
    """Records system audit trail for all significant actions."""

    class Action(models.TextChoices):
        LOGIN = 'LOGIN', 'Login'
        LOGOUT = 'LOGOUT', 'Logout'
        CREATE = 'CREATE', 'Create'
        UPDATE = 'UPDATE', 'Update'
        DELETE = 'DELETE', 'Delete'
        PRICE_CHANGE = 'PRICE_CHANGE', 'Price Change'
        STOCK_ADJUSTMENT = 'STOCK_ADJUSTMENT', 'Stock Adjustment'
        SALE_CREATE = 'SALE_CREATE', 'Sale Create'
        SALE_CANCEL = 'SALE_CANCEL', 'Sale Cancel'
        REFUND = 'REFUND', 'Refund'
        PURCHASE_CREATE = 'PURCHASE_CREATE', 'Purchase Create'
        EXPENSE_CREATE = 'EXPENSE_CREATE', 'Expense Create'
        PERMISSION_CHANGE = 'PERMISSION_CHANGE', 'Permission Change'
        OTHER = 'OTHER', 'Other'

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        'accounts.User',
        null=True,
        on_delete=models.SET_NULL,
        related_name='audit_logs',
        verbose_name='User',
    )
    action = models.CharField(
        max_length=50,
        choices=Action.choices,
        db_index=True,
        verbose_name='Action',
    )
    model_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Model Name',
    )
    object_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Object ID',
    )
    description = models.TextField(verbose_name='Description')
    previous_value = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Previous Value',
    )
    new_value = models.JSONField(
        null=True,
        blank=True,
        verbose_name='New Value',
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP Address',
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='User Agent',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Created At',
    )

    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user'], name='idx_audit_log_user'),
            models.Index(fields=['action'], name='idx_audit_log_action'),
            models.Index(fields=['model_name'], name='idx_audit_log_model_name'),
            models.Index(fields=['created_at'], name='idx_audit_log_created_at'),
        ]

    def __str__(self):
        return f'{self.action} - {self.model_name} - {self.created_at}'
