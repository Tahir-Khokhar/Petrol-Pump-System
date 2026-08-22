import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.fuel.models import FuelType, Tank
from apps.pumps.models import Pump, Nozzle
from apps.sales.models import Sale
from apps.expenses.models import Expense
from apps.employees.models import Employee


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email='admin@test.com',
        password='testpass123',
        first_name='Admin',
        last_name='User',
        role=User.Role.SUPER_ADMIN,
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def cashier_user(db):
    return User.objects.create_user(
        email='cashier@test.com',
        password='testpass123',
        first_name='Cashier',
        last_name='User',
        role=User.Role.CASHIER,
    )


@pytest.fixture
def accountant_user(db):
    return User.objects.create_user(
        email='accountant@test.com',
        password='testpass123',
        first_name='Accountant',
        last_name='User',
        role=User.Role.ACCOUNTANT,
        is_staff=True,
    )


@pytest.fixture
def auth_admin_client(admin_user):
    client = APIClient()
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(admin_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def auth_cashier_client(cashier_user):
    client = APIClient()
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(cashier_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def auth_accountant_client(accountant_user):
    client = APIClient()
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(accountant_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def test_data(db, admin_user):
    """Create test data for report testing."""
    fuel_type = FuelType.objects.create(
        name='Diesel',
        code='DSL',
        current_price=Decimal('90.00'),
        minimum_stock_level=Decimal('500'),
    )
    fuel_type2 = FuelType.objects.create(
        name='Petrol',
        code='PTL',
        current_price=Decimal('100.00'),
        minimum_stock_level=Decimal('500'),
    )

    tank = Tank.objects.create(
        tank_number='T001',
        fuel_type=fuel_type,
        capacity=Decimal('10000'),
        current_quantity=Decimal('5000'),
        status=Tank.Status.ACTIVE,
    )

    pump = Pump.objects.create(
        pump_number='P001',
        name='Pump 1',
        status=Pump.Status.ACTIVE,
    )

    nozzle = Nozzle.objects.create(
        nozzle_number='N001',
        pump=pump,
        fuel_type=fuel_type,
        status='ACTIVE',
    )

    employee = Employee.objects.create(
        user=admin_user,
        employee_id='EMP001',
        name='Admin User',
        job_role=Employee.JobRole.MANAGER,
        hire_date=date.today(),
        status=Employee.Status.ACTIVE,
    )

    # Create some sales
    today = timezone.now()
    for i in range(5):
        Sale.objects.create(
            receipt_number=f'RCP{i:04d}',
            employee=admin_user,
            pump=pump,
            nozzle=nozzle,
            fuel_type=fuel_type if i < 3 else fuel_type2,
            quantity=Decimal('10.00'),
            price_per_unit=fuel_type.current_price if i < 3 else fuel_type2.current_price,
            subtotal=Decimal('900.00') if i < 3 else Decimal('1000.00'),
            total_amount=Decimal('900.00') if i < 3 else Decimal('1000.00'),
            payment_method=Sale.PaymentMethod.CASH if i % 2 == 0 else Sale.PaymentMethod.CARD,
            status=Sale.Status.COMPLETED,
            created_at=today,
        )

    # Create some expenses
    Expense.objects.create(
        category=Expense.Category.ELECTRICITY,
        amount=Decimal('5000'),
        description='Monthly electricity bill',
        expense_date=date.today(),
        created_by=admin_user,
    )
    Expense.objects.create(
        category=Expense.Category.MAINTENANCE,
        amount=Decimal('2000'),
        description='Pump maintenance',
        expense_date=date.today(),
        created_by=admin_user,
    )

    return {
        'fuel_type': fuel_type,
        'fuel_type2': fuel_type2,
        'tank': tank,
        'pump': pump,
        'nozzle': nozzle,
    }


@pytest.mark.django_db
class TestDailySalesReport:
    def test_valid_request(self, auth_admin_client, test_data):
        today_str = date.today().isoformat()
        response = auth_admin_client.get('/api/v1/reports/daily-sales/', {'date': today_str})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        data = response.data['data']
        assert data['total_transactions'] == 5
        assert data['total_sales'] > 0
        assert data['total_liters'] > 0
        assert len(data['sales_by_fuel_type']) > 0

    def test_missing_date_param(self, auth_admin_client):
        response = auth_admin_client.get('/api/v1/reports/daily-sales/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    def test_invalid_date_format(self, auth_admin_client):
        response = auth_admin_client.get('/api/v1/reports/daily-sales/', {'date': 'not-a-date'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cashier_cannot_access(self, auth_cashier_client):
        today_str = date.today().isoformat()
        response = auth_cashier_client.get('/api/v1/reports/daily-sales/', {'date': today_str})
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestMonthlySalesReport:
    def test_valid_request(self, auth_admin_client, test_data):
        today = date.today()
        response = auth_admin_client.get(
            '/api/v1/reports/monthly-sales/',
            {'year': today.year, 'month': today.month},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        data = response.data['data']
        assert data['year'] == today.year
        assert data['month'] == today.month
        assert data['total_revenue'] > 0
        assert 'daily_breakdown' in data

    def test_missing_params(self, auth_admin_client):
        response = auth_admin_client.get('/api/v1/reports/monthly-sales/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_accountant_can_access(self, auth_accountant_client, test_data):
        today = date.today()
        response = auth_accountant_client.get(
            '/api/v1/reports/monthly-sales/',
            {'year': today.year, 'month': today.month},
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestFuelStockReport:
    def test_valid_request(self, auth_admin_client, test_data):
        response = auth_admin_client.get('/api/v1/reports/fuel-stock/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        data = response.data['data']
        assert isinstance(data, list)
        assert len(data) >= 2  # At least Diesel and Petrol
        assert data[0]['closing_stock'] > 0


@pytest.mark.django_db
class TestExpenseReport:
    def test_valid_request(self, auth_admin_client, test_data):
        today_str = date.today().isoformat()
        response = auth_admin_client.get(
            '/api/v1/reports/expenses/',
            {'date_from': today_str, 'date_to': today_str},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        data = response.data['data']
        assert data['total_expenses'] > 0
        assert len(data['expenses_by_category']) > 0

    def test_missing_params(self, auth_admin_client):
        response = auth_admin_client.get('/api/v1/reports/expenses/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_by_category(self, auth_admin_client, test_data):
        today_str = date.today().isoformat()
        response = auth_admin_client.get(
            '/api/v1/reports/expenses/',
            {'date_from': today_str, 'date_to': today_str, 'category': 'ELECTRICITY'},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.data['data']
        assert all(e['category'] == 'ELECTRICITY' for e in data['expenses_by_category'])


@pytest.mark.django_db
class TestDashboard:
    def test_admin_can_access_dashboard(self, auth_admin_client, test_data):
        response = auth_admin_client.get('/api/v1/dashboard/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        data = response.data['data']
        assert 'today_sales' in data
        assert 'current_stock' in data
        assert 'recent_sales' in data
        assert 'sales_by_payment_method' in data

    def test_cashier_can_access_dashboard(self, auth_cashier_client, test_data):
        response = auth_cashier_client.get('/api/v1/dashboard/')
        assert response.status_code == status.HTTP_200_OK

    def test_accountant_can_access_dashboard(self, auth_accountant_client, test_data):
        response = auth_accountant_client.get('/api/v1/dashboard/')
        assert response.status_code == status.HTTP_200_OK

    def test_dashboard_with_date_range(self, auth_admin_client, test_data):
        today_str = date.today().isoformat()
        response = auth_admin_client.get(
            '/api/v1/dashboard/',
            {'date_from': today_str, 'date_to': today_str},
        )
        assert response.status_code == status.HTTP_200_OK
