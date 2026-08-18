import django_filters

from apps.audit_logs.models import AuditLog


class AuditLogFilter(django_filters.FilterSet):
    action = django_filters.CharFilter(field_name='action', lookup_expr='exact')
    model_name = django_filters.CharFilter(field_name='model_name', lookup_expr='exact')
    user = django_filters.UUIDFilter(field_name='user__uuid')
    date_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = AuditLog
        fields = ['action', 'model_name', 'user']

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(description__icontains=value)
