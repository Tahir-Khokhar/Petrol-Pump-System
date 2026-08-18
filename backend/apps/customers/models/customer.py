import uuid

from django.db import models

from apps.accounts.models import User


class Customer(models.Model):
    """Represents a customer of the petrol pump."""

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_profile',
        verbose_name='Linked User',
    )
    full_name = models.CharField(max_length=200, verbose_name='Full Name')
    phone = models.CharField(max_length=20, db_index=True, verbose_name='Phone Number')
    email = models.EmailField(blank=True, verbose_name='Email Address')
    address = models.TextField(blank=True, verbose_name='Address')
    is_corporate = models.BooleanField(default=False, verbose_name='Is Corporate')
    company_name = models.CharField(max_length=300, blank=True, verbose_name='Company Name')
    tax_number = models.CharField(max_length=100, blank=True, verbose_name='Tax Number')
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Credit Limit',
    )
    outstanding_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Outstanding Balance',
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
        db_table = 'customers'
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone'], name='idx_customer_phone'),
            models.Index(fields=['email'], name='idx_customer_email'),
            models.Index(fields=['is_corporate'], name='idx_customer_is_corporate'),
            models.Index(fields=['status'], name='idx_customer_status'),
        ]

    def __str__(self):
        return self.full_name
