import django_filters
from django.db import models as django_models

from apps.employees.models import Employee


class EmployeeFilter(django_filters.FilterSet):
    """FilterSet for employees."""

    search = django_filters.CharFilter(method='filter_search')
    assigned_pump = django_filters.UUIDFilter(field_name='assigned_pump__uuid')

    class Meta:
        model = Employee
        fields = {
            'job_role': ['exact'],
            'status': ['exact'],
        }

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            django_models.Q(name__icontains=value)
            | django_models.Q(employee_id__icontains=value)
            | django_models.Q(phone__icontains=value)
        )
