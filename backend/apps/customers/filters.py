import django_filters
from django.db import models as django_models

from apps.customers.models import Customer, Vehicle


class CustomerFilter(django_filters.FilterSet):
    """FilterSet for customers."""

    search = django_filters.CharFilter(method='filter_search')
    created_at_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Customer
        fields = {
            'status': ['exact'],
            'is_corporate': ['exact'],
        }

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            django_models.Q(full_name__icontains=value)
            | django_models.Q(phone__icontains=value)
            | django_models.Q(company_name__icontains=value)
        )


class VehicleFilter(django_filters.FilterSet):
    """FilterSet for vehicles."""

    customer = django_filters.UUIDFilter(field_name='customer__uuid')
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Vehicle
        fields = {
            'vehicle_type': ['exact'],
            'status': ['exact'],
        }

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(registration_number__icontains=value)
