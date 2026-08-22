import django_filters

from apps.shifts.models import MeterReading, Shift


class ShiftFilter(django_filters.FilterSet):
    """Filter set for shifts."""
    date_from = django_filters.DateTimeFilter(field_name='start_time', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='start_time', lookup_expr='lte')

    class Meta:
        model = Shift
        fields = {
            'employee': ['exact'],
            'pump': ['exact'],
            'status': ['exact'],
        }


class MeterReadingFilter(django_filters.FilterSet):
    """Filter set for meter readings."""
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = MeterReading
        fields = {
            'shift': ['exact'],
            'nozzle': ['exact'],
        }
