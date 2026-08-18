import uuid

from django.db import models, transaction

from apps.accounts.models import User
from apps.pumps.models import Pump


class Employee(models.Model):
    """Represents an employee profile linked to a User."""

    class JobRole(models.TextChoices):
        MANAGER = 'MANAGER', 'Manager'
        CASHIER = 'CASHIER', 'Cashier'
        PUMP_ATTENDANT = 'PUMP_ATTENDANT', 'Pump Attendant'
        INVENTORY_MANAGER = 'INVENTORY_MANAGER', 'Inventory Manager'
        ACCOUNTANT = 'ACCOUNTANT', 'Accountant'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        TERMINATED = 'TERMINATED', 'Terminated'

    # Mapping from Employee.JobRole to User.Role for matching
    ROLE_MAPPING = {
        JobRole.MANAGER: User.Role.PUMP_MANAGER,
        JobRole.CASHIER: User.Role.CASHIER,
        JobRole.PUMP_ATTENDANT: User.Role.PUMP_ATTENDANT,
        JobRole.INVENTORY_MANAGER: User.Role.INVENTORY_MANAGER,
        JobRole.ACCOUNTANT: User.Role.ACCOUNTANT,
    }

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        verbose_name='User',
    )
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Employee ID',
    )
    name = models.CharField(max_length=200, verbose_name='Full Name')
    phone = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='Phone Number',
    )
    email = models.EmailField(
        blank=True,
        default='',
        verbose_name='Email',
    )
    job_role = models.CharField(
        max_length=20,
        choices=JobRole.choices,
        verbose_name='Job Role',
    )
    salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Salary',
    )
    hire_date = models.DateField(verbose_name='Hire Date')
    assigned_pump = models.ForeignKey(
        Pump,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='employees',
        verbose_name='Assigned Pump',
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
        db_table = 'employees'
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee_id'], name='idx_employee_employee_id'),
            models.Index(fields=['job_role'], name='idx_employee_job_role'),
            models.Index(fields=['status'], name='idx_employee_status'),
            models.Index(fields=['assigned_pump'], name='idx_employee_assigned_pump'),
        ]

    def __str__(self):
        return self.employee_id

    def save(self, *args, **kwargs):
        """Override save to sync user role with job_role."""
        from django.db import transaction

        with transaction.atomic():
            # Match user role to job_role if mapping exists
            mapped_role = self.ROLE_MAPPING.get(self.job_role)
            if mapped_role and self.user.role != mapped_role:
                self.user.role = mapped_role
                self.user.save(update_fields=['role'])
            super().save(*args, **kwargs)
