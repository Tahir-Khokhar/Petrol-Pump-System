import django_filters
from django.db import models as django_models

from apps.suppliers.models import Supplier


class SupplierFilter(django_filters.FilterSet):
    """FilterSet for suppliers."""

    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Supplier
        fields = {
            'status': ['exact'],
        }

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            django_models.Q(company_name__icontains=value)
            | django_models.Q(contact_person__icontains=value)
            | django_models.Q(phone__icontains=value)
        )
