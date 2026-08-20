import django_filters
from django.db import models as django_models

from apps.pumps.models import Nozzle, Pump


class PumpFilter(django_filters.FilterSet):
    """FilterSet for pumps."""

    fuel_type = django_filters.UUIDFilter(field_name='fuel_types__uuid')
    assigned_employee = django_filters.UUIDFilter(field_name='assigned_employee__uuid')
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Pump
        fields = {
            'status': ['exact'],
        }

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            django_models.Q(name__icontains=value) | django_models.Q(pump_number__icontains=value)
        )


class NozzleFilter(django_filters.FilterSet):
    """FilterSet for nozzles."""

    pump = django_filters.UUIDFilter(field_name='pump__uuid')
    fuel_type = django_filters.UUIDFilter(field_name='fuel_type__uuid')
    status = django_filters.CharFilter(field_name='status')

    class Meta:
        model = Nozzle
        fields = {
            'pump': ['exact'],
            'fuel_type': ['exact'],
            'status': ['exact'],
        }
