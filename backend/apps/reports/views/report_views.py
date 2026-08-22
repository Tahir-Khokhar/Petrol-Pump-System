from datetime import datetime

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.reports.permissions import CanViewReports
from apps.reports.services import (
    daily_sales_report,
    monthly_sales_report,
    fuel_stock_report,
    employee_performance_report,
    pump_performance_report,
    expense_report,
)


@extend_schema(
    summary='Daily sales report',
    description='Get sales report for a specific date. Accepts optional pump and fuel_type filters.',
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, CanViewReports])
def daily_sales_view(request):
    date_str = request.query_params.get('date')
    if not date_str:
        return Response({
            'success': False,
            'message': 'Query parameter "date" is required (YYYY-MM-DD).',
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return Response({
            'success': False,
            'message': 'Invalid date format. Use YYYY-MM-DD.',
        }, status=status.HTTP_400_BAD_REQUEST)

    pump_id = request.query_params.get('pump')
    fuel_type_id = request.query_params.get('fuel_type')

    data = daily_sales_report(date, pump_id=pump_id, fuel_type_id=fuel_type_id)
    return Response({'success': True, 'data': data})


@extend_schema(
    summary='Monthly sales report',
    description='Get sales report for a specific month. Requires year and month parameters.',
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, CanViewReports])
def monthly_sales_view(request):
    year_str = request.query_params.get('year')
    month_str = request.query_params.get('month')

    if not year_str or not month_str:
        return Response({
            'success': False,
            'message': 'Query parameters "year" and "month" are required.',
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        year = int(year_str)
        month = int(month_str)
        if month < 1 or month > 12:
            raise ValueError
    except (ValueError, TypeError):
        return Response({
            'success': False,
            'message': 'Invalid year or month. Year must be an integer, month 1-12.',
        }, status=status.HTTP_400_BAD_REQUEST)

    data = monthly_sales_report(year, month)
    return Response({'success': True, 'data': data})


@extend_schema(
    summary='Fuel stock report',
    description='Get current fuel stock levels with purchase/sale summaries. Optional fuel_type filter.',
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, CanViewReports])
def fuel_stock_view(request):
    fuel_type_id = request.query_params.get('fuel_type')
    data = fuel_stock_report(fuel_type_id=fuel_type_id)
    return Response({'success': True, 'data': data})


@extend_schema(
    summary='Employee performance report',
    description='Get employee sales performance. Optional employee, date_from, date_to filters.',
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, CanViewReports])
def employee_performance_view(request):
    employee_id = request.query_params.get('employee')
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')

    data = employee_performance_report(
        employee_id=employee_id,
        date_from=date_from,
        date_to=date_to,
    )
    return Response({'success': True, 'data': data})


@extend_schema(
    summary='Pump performance report',
    description='Get pump sales performance. Optional pump, date_from, date_to filters.',
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, CanViewReports])
def pump_performance_view(request):
    pump_id = request.query_params.get('pump')
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')

    data = pump_performance_report(
        pump_id=pump_id,
        date_from=date_from,
        date_to=date_to,
    )
    return Response({'success': True, 'data': data})


@extend_schema(
    summary='Expense report',
    description='Get expense report for a date range. Required: date_from, date_to. Optional: category.',
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, CanViewReports])
def expense_report_view(request):
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')

    if not date_from or not date_to:
        return Response({
            'success': False,
            'message': 'Query parameters "date_from" and "date_to" are required (YYYY-MM-DD).',
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        datetime.strptime(date_from, '%Y-%m-%d')
        datetime.strptime(date_to, '%Y-%m-%d')
    except (ValueError, TypeError):
        return Response({
            'success': False,
            'message': 'Invalid date format. Use YYYY-MM-DD.',
        }, status=status.HTTP_400_BAD_REQUEST)

    category = request.query_params.get('category')
    data = expense_report(date_from, date_to, category=category)
    return Response({'success': True, 'data': data})
