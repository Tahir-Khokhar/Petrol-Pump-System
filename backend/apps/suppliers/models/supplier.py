import uuid
import re

from django.db import models


class Supplier(models.Model):
    """Represents a fuel/product supplier."""

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    company_name = models.CharField(
        max_length=300,
        verbose_name='Company Name',
    )
    contact_person = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='Contact Person',
    )
    phone = models.CharField(
        max_length=20,
        db_index=True,
        verbose_name='Phone Number',
    )
    email = models.EmailField(
        blank=True,
        default='',
        verbose_name='Email',
    )
    address = models.TextField(
        blank=True,
        default='',
        verbose_name='Address',
    )
    tax_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Tax Number',
    )
    bank_details = models.TextField(
        blank=True,
        default='',
        verbose_name='Bank Details',
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
        db_table = 'suppliers'
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company_name'], name='idx_supplier_company_name'),
            models.Index(fields=['phone'], name='idx_supplier_phone'),
            models.Index(fields=['status'], name='idx_supplier_status'),
        ]

    def __str__(self):
        return self.company_name
