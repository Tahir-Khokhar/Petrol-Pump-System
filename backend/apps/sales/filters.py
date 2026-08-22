import django_filters
from django.db import models as django_models

from apps.sales.models import Refund, Sale


class SaleFilter(django_filters.FilterSet):
    """Filter set for sales."""

    date_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Sale
        fields = {
            'payment_method': ['exact'],
            'status': ['exact'],
            'pump': ['exact'],
            'fuel_type': ['exact'],
            'employee': ['exact'],
            'customer': ['exact'],
        }

    def filter_search(self, queryset, name, value):
        """Search on receipt_number and customer name."""
        if not value:
            return queryset
        return queryset.filter(
            django_models.Q(receipt_number__icontains=value)
            | django_models.Q(customer__full_name__icontains=value)
        )


class RefundFilter(django_filters.FilterSet):
    """Filter set for refunds."""

    date_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Refund
        fields = {
            'sale': ['exact'],
            'status': ['exact'],
            'processed_by': ['exact'],
        }
