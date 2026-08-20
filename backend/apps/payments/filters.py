import django_filters

from apps.payments.models import Payment


class PaymentFilter(django_filters.FilterSet):
    """Filter set for payments."""

    date_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Payment
        fields = {
            'sale': ['exact'],
            'status': ['exact'],
            'payment_method': ['exact'],
            'processed_by': ['exact'],
        }
