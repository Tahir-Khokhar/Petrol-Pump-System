import django_filters

from apps.fuel.models import FuelType, Tank


class FuelTypeFilter(django_filters.FilterSet):
    """FilterSet for fuel types."""

    name = django_filters.CharFilter(lookup_expr='icontains')
    code = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = FuelType
        fields = {
            'is_active': ['exact'],
            'name': ['exact', 'icontains'],
            'code': ['exact'],
        }


class TankFilter(django_filters.FilterSet):
    """FilterSet for tanks."""

    fuel_type = django_filters.UUIDFilter(field_name='fuel_type__uuid')
    status = django_filters.CharFilter(field_name='status')
    location = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Tank
        fields = {
            'fuel_type': ['exact'],
            'status': ['exact'],
            'location': ['exact', 'icontains'],
        }
