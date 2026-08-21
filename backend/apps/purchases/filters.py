import django_filters
from django.db import models as django_models

from apps.purchases.models import Purchase


class PurchaseFilter(django_filters.FilterSet):
    """Filter set for purchases."""
    date_from = django_filters.DateFilter(field_name='purchase_date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='purchase_date', lookup_expr='lte')
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Purchase
        fields = {
            'supplier': ['exact'],
            'fuel_type': ['exact'],
            'tank': ['exact'],
            'payment_status': ['exact'],
            'created_by': ['exact'],
        }

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            django_models.Q(purchase_number__icontains=value)
            | django_models.Q(invoice_number__icontains=value)
        )
