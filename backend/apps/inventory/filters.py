import django_filters
from django.db import models as django_models

from apps.inventory.models import InventoryItem, InventoryTransaction


class InventoryItemFilter(django_filters.FilterSet):
    """Filter set for inventory items."""
    is_low_stock = django_filters.BooleanFilter(method='filter_is_low_stock')
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = InventoryItem
        fields = {
            'category': ['exact'],
            'is_active': ['exact'],
        }

    def filter_is_low_stock(self, queryset, name, value):
        if value is None:
            return queryset
        if value:
            return queryset.filter(
                current_stock__lte=django_models.F('minimum_stock_level')
            )
        return queryset.filter(
            current_stock__gt=django_models.F('minimum_stock_level')
        )

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            django_models.Q(name__icontains=value)
            | django_models.Q(sku__icontains=value)
        )


class InventoryTransactionFilter(django_filters.FilterSet):
    """Filter set for inventory transactions."""
    date_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = InventoryTransaction
        fields = {
            'inventory_item': ['exact'],
            'transaction_type': ['exact'],
        }
