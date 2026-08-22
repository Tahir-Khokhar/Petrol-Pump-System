from decimal import Decimal

from django.db.models import (
    Case,
    Count,
    DecimalField,
    F,
    Q,
    Sum,
    Value,
    When,
)
from django.utils import timezone

from apps.expenses.models import Expense
from apps.fuel.models import FuelType, Tank
from apps.inventory.models import InventoryTransaction
from apps.purchases.models import Purchase
from apps.pumps.models import Pump
from apps.sales.models import Sale
from apps.shifts.models import Shift


def _decimal(val):
    """Safely convert a value to Decimal, defaulting to 0."""
    if val is None:
        return Decimal('0')
    return Decimal(str(val))


def _float(val):
    """Convert Decimal to float for JSON serialization."""
    if val is None:
        return 0.0
    return float(val)


def daily_sales_report(date, pump_id=None, fuel_type_id=None):
    """Generate daily sales report for a given date."""
    start = timezone.make_aware(timezone.datetime.combine(date, timezone.datetime.min.time()))
    end = timezone.make_aware(timezone.datetime.combine(date, timezone.datetime.max.time()))

    qs = Sale.objects.filter(
        created_at__gte=start,
        created_at__lte=end,
        status=Sale.Status.COMPLETED,
    )
    if pump_id:
        qs = qs.filter(pump_id=pump_id)
    if fuel_type_id:
        qs = qs.filter(fuel_type_id=fuel_type_id)

    totals = qs.aggregate(
        total_sales=Sum('total_amount', output_field=DecimalField()),
        total_liters=Sum('quantity', output_field=DecimalField()),
        total_transactions=Count('uuid'),
        cash_sales=Sum(
            Case(
                When(payment_method=Sale.PaymentMethod.CASH, then=F('total_amount')),
                default=Value(Decimal('0')),
                output_field=DecimalField(),
            )
        ),
        card_sales=Sum(
            Case(
                When(payment_method=Sale.PaymentMethod.CARD, then=F('total_amount')),
                default=Value(Decimal('0')),
                output_field=DecimalField(),
            )
        ),
        digital_wallet_sales=Sum(
            Case(
                When(payment_method=Sale.PaymentMethod.DIGITAL_WALLET, then=F('total_amount')),
                default=Value(Decimal('0')),
                output_field=DecimalField(),
            )
        ),
        bank_transfer_sales=Sum(
            Case(
                When(payment_method=Sale.PaymentMethod.BANK_TRANSFER, then=F('total_amount')),
                default=Value(Decimal('0')),
                output_field=DecimalField(),
            )
        ),
    )

    # Sales by fuel type
    fuel_breakdown = qs.values(
        'fuel_type__name',
    ).annotate(
        quantity=Sum('quantity', output_field=DecimalField()),
        revenue=Sum('total_amount', output_field=DecimalField()),
    ).order_by('fuel_type__name')

    return {
        'date': str(date),
        'total_sales': _float(totals['total_sales']),
        'total_liters': _float(totals['total_liters']),
        'total_transactions': totals['total_transactions'] or 0,
        'cash_sales': _float(totals['cash_sales']),
        'card_sales': _float(totals['card_sales']),
        'digital_wallet_sales': _float(totals['digital_wallet_sales']),
        'bank_transfer_sales': _float(totals['bank_transfer_sales']),
        'sales_by_fuel_type': [
            {
                'fuel_type': fb['fuel_type__name'],
                'quantity': _float(fb['quantity']),
                'revenue': _float(fb['revenue']),
            }
            for fb in fuel_breakdown
        ],
    }


def monthly_sales_report(year, month):
    """Generate monthly sales report."""
    from datetime import datetime
    import calendar

    first_day = timezone.make_aware(datetime(year, month, 1))
    last_day_num = calendar.monthrange(year, month)[1]
    last_day = timezone.make_aware(datetime(year, month, last_day_num, 23, 59, 59, 999999))

    # Revenue data
    sales_qs = Sale.objects.filter(
        created_at__gte=first_day,
        created_at__lte=last_day,
        status=Sale.Status.COMPLETED,
    )
    sales_totals = sales_qs.aggregate(
        total_revenue=Sum('total_amount', output_field=DecimalField()),
        total_liters=Sum('quantity', output_field=DecimalField()),
        total_transactions=Count('uuid'),
    )

    # Expenses
    expenses_qs = Expense.objects.filter(
        expense_date__gte=first_day.date(),
        expense_date__lte=last_day.date(),
    )
    total_expenses = expenses_qs.aggregate(
        total=Sum('amount', output_field=DecimalField()),
    )['total']

    total_revenue = _decimal(sales_totals['total_revenue'])
    profit_estimate = total_revenue - _decimal(total_expenses)

    # Sales by fuel type
    fuel_breakdown = sales_qs.values('fuel_type__name').annotate(
        quantity=Sum('quantity', output_field=DecimalField()),
        revenue=Sum('total_amount', output_field=DecimalField()),
    ).order_by('fuel_type__name')

    # Daily breakdown
    daily = sales_qs.annotate(
        day=F('created_at__date'),
    ).values('day').annotate(
        revenue=Sum('total_amount', output_field=DecimalField()),
        liters=Sum('quantity', output_field=DecimalField()),
        transactions=Count('uuid'),
    ).order_by('day')

    return {
        'year': year,
        'month': month,
        'total_revenue': _float(total_revenue),
        'total_expenses': _float(total_expenses),
        'profit_estimate': _float(profit_estimate),
        'total_liters': _float(sales_totals['total_liters']),
        'total_transactions': sales_totals['total_transactions'] or 0,
        'sales_by_fuel_type': [
            {
                'fuel_type': fb['fuel_type__name'],
                'quantity': _float(fb['quantity']),
                'revenue': _float(fb['revenue']),
            }
            for fb in fuel_breakdown
        ],
        'daily_breakdown': [
            {
                'date': str(d['day']),
                'revenue': _float(d['revenue']),
                'liters': _float(d['liters']),
                'transactions': d['transactions'],
            }
            for d in daily
        ],
    }


def fuel_stock_report(fuel_type_id=None):
    """Generate fuel stock report with opening stock, purchases, sales, adjustments."""
    if fuel_type_id:
        fuel_types = FuelType.objects.filter(uuid=fuel_type_id)
    else:
        fuel_types = FuelType.objects.filter(is_active=True)

    report = []
    for ft in fuel_types:
        # Get active tank for this fuel type
        tank = Tank.objects.filter(
            fuel_type=ft, status=Tank.Status.ACTIVE,
        ).first()

        closing_stock = tank.current_quantity if tank else Decimal('0')

        # Total purchased (from Purchase model)
        total_purchased = Purchase.objects.filter(
            fuel_type=ft,
        ).aggregate(
            total=Sum('quantity', output_field=DecimalField()),
        )['total'] or Decimal('0')

        # Total sold (from Sale model - completed only)
        total_sold = Sale.objects.filter(
            fuel_type=ft,
            status=Sale.Status.COMPLETED,
        ).aggregate(
            total=Sum('quantity', output_field=DecimalField()),
        )['total'] or Decimal('0')

        # Opening stock: estimated as closing_stock + sold - purchased
        opening_stock = closing_stock + total_sold - total_purchased

        report.append({
            'fuel_type': ft.name,
            'opening_stock': _float(opening_stock),
            'total_purchased': _float(total_purchased),
            'total_sold': _float(total_sold),
            'adjustments': 0.0,
            'closing_stock': _float(closing_stock),
        })

    return report


def employee_performance_report(employee_id=None, date_from=None, date_to=None):
    """Generate employee performance report."""
    qs = Sale.objects.filter(status=Sale.Status.COMPLETED)

    if employee_id:
        qs = qs.filter(employee_id=employee_id)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    report = qs.values(
        'employee__uuid',
        'employee__first_name',
        'employee__last_name',
        'employee__email',
    ).annotate(
        total_sales=Sum('total_amount', output_field=DecimalField()),
        total_transactions=Count('uuid'),
        total_liters=Sum('quantity', output_field=DecimalField()),
        average_sale=Sum('total_amount', output_field=DecimalField())
                    / Count('uuid'),
    ).order_by('-total_sales')

    result = []
    for r in report:
        emp_uuid = r['employee__uuid']

        # Get shift differences for this employee
        shift_qs = Shift.objects.filter(employee_id=emp_uuid)
        if date_from:
            shift_qs = shift_qs.filter(start_time__date__gte=date_from)
        if date_to:
            shift_qs = shift_qs.filter(start_time__date__lte=date_to)

        shift_data = shift_qs.values('uuid', 'pump__pump_number', 'cash_difference', 'status')
        shift_differences = [
            {
                'shift_uuid': str(s['uuid']),
                'pump': s['pump__pump_number'],
                'cash_difference': _float(s['cash_difference']),
                'status': s['status'],
            }
            for s in shift_data
        ]

        result.append({
            'employee': f"{r['employee__first_name']} {r['employee__last_name']}",
            'employee_email': r['employee__email'],
            'total_sales': _float(r['total_sales']),
            'total_transactions': r['total_transactions'],
            'total_liters': _float(r['total_liters']),
            'average_sale': _float(r['average_sale']),
            'shift_differences': shift_differences,
        })

    return result


def pump_performance_report(pump_id=None, date_from=None, date_to=None):
    """Generate pump performance report."""
    qs = Sale.objects.filter(status=Sale.Status.COMPLETED)

    if pump_id:
        qs = qs.filter(pump_id=pump_id)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    report = qs.values(
        'pump__uuid',
        'pump__pump_number',
    ).annotate(
        total_revenue=Sum('total_amount', output_field=DecimalField()),
        total_liters=Sum('quantity', output_field=DecimalField()),
        total_transactions=Count('uuid'),
    ).order_by('-total_revenue')

    result = []
    for r in report:
        pump_uuid = r['pump__uuid']

        # Fuel type breakdown for this pump
        pump_qs = qs.filter(pump_id=pump_uuid)
        fuel_breakdown = pump_qs.values('fuel_type__name').annotate(
            quantity=Sum('quantity', output_field=DecimalField()),
            revenue=Sum('total_amount', output_field=DecimalField()),
        ).order_by('fuel_type__name')

        result.append({
            'pump': r['pump__pump_number'],
            'total_revenue': _float(r['total_revenue']),
            'total_liters': _float(r['total_liters']),
            'total_transactions': r['total_transactions'],
            'sales_by_fuel_type': [
                {
                    'fuel_type': fb['fuel_type__name'],
                    'quantity': _float(fb['quantity']),
                    'revenue': _float(fb['revenue']),
                }
                for fb in fuel_breakdown
            ],
        })

    return result


def expense_report(date_from, date_to, category=None):
    """Generate expense report for a date range."""
    qs = Expense.objects.filter(
        expense_date__gte=date_from,
        expense_date__lte=date_to,
    )
    if category:
        qs = qs.filter(category=category)

    total = qs.aggregate(
        total=Sum('amount', output_field=DecimalField()),
    )['total']

    # By category
    by_category = qs.values('category').annotate(
        amount=Sum('amount', output_field=DecimalField()),
    ).order_by('-amount')

    # Daily expenses
    daily = qs.values('expense_date').annotate(
        amount=Sum('amount', output_field=DecimalField()),
    ).order_by('expense_date')

    return {
        'total_expenses': _float(total),
        'expenses_by_category': [
            {
                'category': ec['category'],
                'amount': _float(ec['amount']),
            }
            for ec in by_category
        ],
        'daily_expenses': [
            {
                'date': str(d['expense_date']),
                'amount': _float(d['amount']),
            }
            for d in daily
        ],
    }
