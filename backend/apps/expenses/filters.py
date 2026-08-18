import django_filters

from apps.expenses.models import Expense


class ExpenseFilter(django_filters.FilterSet):
    """Filter set for expenses."""
    date_from = django_filters.DateFilter(field_name='expense_date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='expense_date', lookup_expr='lte')

    class Meta:
        model = Expense
        fields = {
            'category': ['exact'],
            'payment_method': ['exact'],
            'employee': ['exact'],
            'created_by': ['exact'],
        }
