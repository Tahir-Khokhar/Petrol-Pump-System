from django.urls import path

from apps.reports.views.report_views import (
    daily_sales_view,
    monthly_sales_view,
    fuel_stock_view,
    employee_performance_view,
    pump_performance_view,
    expense_report_view,
)

urlpatterns = [
    path('daily-sales/', daily_sales_view, name='daily-sales-report'),
    path('monthly-sales/', monthly_sales_view, name='monthly-sales-report'),
    path('fuel-stock/', fuel_stock_view, name='fuel-stock-report'),
    path('employee-performance/', employee_performance_view, name='employee-performance-report'),
    path('pump-performance/', pump_performance_view, name='pump-performance-report'),
    path('expenses/', expense_report_view, name='expense-report'),
]
