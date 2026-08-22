from decimal import Decimal

from django.db.models import (
    Case,
    Count,
    DecimalField,
    F,
    Sum,
    Value,
    When,
)
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.expenses.models import Expense
from apps.fuel.models import FuelType, Tank
from apps.inventory.models import InventoryItem
from apps.pumps.models import Pump
from apps.reports.permissions import CanViewDashboard
from apps.sales.models import Sale


def _float(val):
    """Convert Decimal to float for JSON serialization."""
    if val is None:
        return 0.0
    return float(val)


def _build_dashboard_data(date_from, date_to):
    """Build all dashboard data using optimized queries."""
    today = timezone.now().date()

    # Default to last 7 days if no range provided
    if not date_from and not date_to:
        from datetime import timedelta
        start = timezone.make_aware(
            timezone.datetime.combine(today - timedelta(days=7), timezone.datetime.min.time())
        )
        end = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.max.time())
        )
    else:
        from datetime import datetime
        start = timezone.make_aware(
            datetime.combine(datetime.strptime(date_from, '%Y-%m-%d').date(), timezone.datetime.min.time())
        )
        end = timezone.make_aware(
            datetime.combine(datetime.strptime(date_to, '%Y-%m-%d').date(), timezone.datetime.max.time())
        )

    # Sales aggregation
    sales_qs = Sale.objects.filter(
        created_at__gte=start,
        created_at__lte=end,
        status=Sale.Status.COMPLETED,
    )
    sales_totals = sales_qs.aggregate(
        today_sales=Sum('total_amount', output_field=DecimalField()),
        today_transactions=Count('uuid'),
        fuel_sold=Sum('quantity', output_field=DecimalField()),
        cash=Sum(
            Case(
                When(payment_method=Sale.PaymentMethod.CASH, then=F('total_amount')),
                default=Value(Decimal('0')),
                output_field=DecimalField(),
            )
        ),
        card=Sum(
            Case(
                When(payment_method=Sale.PaymentMethod.CARD, then=F('total_amount')),
                default=Value(Decimal('0')),
                output_field=DecimalField(),
            )
        ),
        digital_wallet=Sum(
            Case(
                When(payment_method=Sale.PaymentMethod.DIGITAL_WALLET, then=F('total_amount')),
                default=Value(Decimal('0')),
                output_field=DecimalField(),
            )
        ),
        bank_transfer=Sum(
            Case(
                When(payment_method=Sale.PaymentMethod.BANK_TRANSFER, then=F('total_amount')),
                default=Value(Decimal('0')),
                output_field=DecimalField(),
            )
        ),
        credit=Sum(
            Case(
                When(payment_method=Sale.PaymentMethod.CREDIT, then=F('total_amount')),
                default=Value(Decimal('0')),
                output_field=DecimalField(),
            )
        ),
        other_pm=Sum(
            Case(
                When(payment_method=Sale.PaymentMethod.OTHER, then=F('total_amount')),
                default=Value(Decimal('0')),
                output_field=DecimalField(),
            )
        ),
    )

    # Payment method breakdown
    sales_by_payment_method = {
        'CASH': _float(sales_totals['cash']),
        'CARD': _float(sales_totals['card']),
        'DIGITAL_WALLET': _float(sales_totals['digital_wallet']),
        'BANK_TRANSFER': _float(sales_totals['bank_transfer']),
        'CREDIT': _float(sales_totals['credit']),
        'OTHER': _float(sales_totals['other_pm']),
    }

    # Top fuel types by liters
    top_fuel_types = list(
        sales_qs.values('fuel_type__name').annotate(
            liters=Sum('quantity', output_field=DecimalField()),
        ).order_by('-liters')[:3]
    )
    top_fuel_types = [
        {'fuel_type': ft['fuel_type__name'], 'liters': _float(ft['liters'])}
        for ft in top_fuel_types
    ]

    # Recent sales (last 5)
    recent_sales = list(
        Sale.objects.filter(status=Sale.Status.COMPLETED).order_by('-created_at')[:5].values(
            'uuid', 'receipt_number', 'total_amount', 'payment_method', 'created_at'
        )
    )
    recent_sales = [
        {
            'id': str(rs['uuid']),
            'receipt_number': rs['receipt_number'],
            'amount': _float(rs['total_amount']),
            'payment_method': rs['payment_method'],
            'time': rs['created_at'].isoformat(),
        }
        for rs in recent_sales
    ]

    # Current fuel stock
    tanks = Tank.objects.filter(status=Tank.Status.ACTIVE).select_related('fuel_type')
    current_stock = []
    for tank in tanks:
        capacity = float(tank.capacity) if tank.capacity else 1
        qty = float(tank.current_quantity) if tank.current_quantity else 0
        percentage = round((qty / capacity) * 100, 1) if capacity > 0 else 0
        current_stock.append({
            'fuel_type': tank.fuel_type.name,
            'current_quantity': qty,
            'capacity': capacity,
            'percentage': percentage,
        })

    # Low stock inventory items
    low_stock_count = InventoryItem.objects.filter(
        is_active=True,
    ).filter(
        current_stock__lte=F('minimum_stock_level')
    ).count()

    # Expenses in selected period
    expenses_qs = Expense.objects.filter(
        expense_date__gte=today - timedelta(days=7),
        expense_date__lte=today,
    ) if not date_from and not date_to else Expense.objects.filter(
        expense_date__gte=datetime.strptime(date_from, '%Y-%m-%d').date(),
        expense_date__lte=datetime.strptime(date_to, '%Y-%m-%d').date(),
    )
    today_expenses = expenses_qs.aggregate(
        total=Sum('amount', output_field=DecimalField()),
    )['total']

    # Active pumps
    active_pumps = Pump.objects.filter(status=Pump.Status.ACTIVE).count()

    # Active employees (cashiers and pump attendants)
    active_employees = User.objects.filter(
        role__in=(User.Role.CASHIER, User.Role.PUMP_ATTENDANT),
        is_active=True,
    ).count()

    return {
        'period_sales': _float(sales_totals['today_sales']),
        'period_transactions': sales_totals['today_transactions'] or 0,
        'fuel_sold_period': _float(sales_totals['fuel_sold']),
        'current_stock': current_stock,
        'low_stock_items': low_stock_count,
        'period_expenses': _float(today_expenses),
        'active_pumps': active_pumps,
        'active_employees': active_employees,
        'recent_sales': recent_sales,
        'sales_by_payment_method': sales_by_payment_method,
        'top_fuel_types': top_fuel_types,
    }


@extend_schema(
    summary='Dashboard overview',
    description='Get dashboard summary with sales, stock, expenses, and activity data. Accepts optional date_from/date_to.',
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, CanViewDashboard])
def dashboard_view(request):
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')

    if date_from and date_to:
        try:
            from datetime import datetime
            datetime.strptime(date_from, '%Y-%m-%d')
            datetime.strptime(date_to, '%Y-%m-%d')
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'message': 'Invalid date format. Use YYYY-MM-DD.',
            }, status=status.HTTP_400_BAD_REQUEST)
    elif date_from or date_to:
        return Response({
            'success': False,
            'message': 'Both date_from and date_to are required if either is provided.',
        }, status=status.HTTP_400_BAD_REQUEST)

    data = _build_dashboard_data(date_from, date_to)
    return Response({'success': True, 'data': data})
