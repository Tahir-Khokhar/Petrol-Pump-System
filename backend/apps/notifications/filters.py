import django_filters

from apps.notifications.models import Notification


class NotificationFilter(django_filters.FilterSet):
    is_read = django_filters.BooleanFilter(field_name='is_read')
    notification_type = django_filters.CharFilter(field_name='notification_type', lookup_expr='exact')

    class Meta:
        model = Notification
        fields = ['is_read', 'notification_type']
