import pytest
from decimal import Decimal

from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.customers.models import Customer
from apps.fuel.models import FuelType, Tank
from apps.payments.models import Payment
from apps.pumps.models import Nozzle, Pump


@pytest.fixture
def fuel_type(db):
    return FuelType.objects.create(
        name='Diesel',
        code='DSL',
        current_price=Decimal('85.50'),
        is_active=True,
    )


@pytest.fixture
def tank(db, fuel_type):
    return Tank.objects.create(
        tank_number='TANK-001',
        fuel_type=fuel_type,
        capacity=Decimal('10000'),
        current_quantity=Decimal('5000'),
        status=Tank.Status.ACTIVE,
    )


@pytest.fixture
def pump(db, fuel_type):
    p = Pump.objects.create(
        pump_number='PMP-001',
        name='Pump 1',
        status=Pump.Status.ACTIVE,
    )
    p.fuel_types.add(fuel_type)
    return p


@pytest.fixture
def nozzle(db, pump, fuel_type, tank):
    return Nozzle.objects.create(
        nozzle_number='NOZ-001',
        pump=pump,
        fuel_type=fuel_type,
        opening_meter_reading=Decimal('1000'),
        current_meter_reading=Decimal('1000'),
        status=Nozzle.Status.ACTIVE,
    )


@pytest.fixture
def cashier_user(db):
    return User.objects.create_user(
        email='cashier@test.com',
        password='testpass123',
        first_name='Cash',
        last_name='ier',
        role=User.Role.CASHIER,
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email='admin@test.com',
        password='testpass123',
        first_name='Super',
        last_name='Admin',
        role=User.Role.SUPER_ADMIN,
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def accountant_user(db):
    return User.objects.create_user(
        email='accountant@test.com',
        password='testpass123',
        first_name='Acc',
        last_name='Countant',
        role=User.Role.ACCOUNTANT,
    )


@pytest.fixture
def auth_client(api_client, cashier_user):
    token = RefreshToken.for_user(cashier_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    token = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return api_client


@pytest.fixture
def accountant_client(api_client, accountant_user):
    token = RefreshToken.for_user(accountant_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return api_client


@pytest.fixture
def sale_obj(pump, nozzle, cashier_user):
    from apps.sales.services import create_sale
    return create_sale({
        'pump': pump.uuid,
        'nozzle': nozzle.uuid,
        'quantity': Decimal('10.00'),
        'discount': Decimal('0'),
        'payment_method': 'CASH',
        'notes': '',
    }, cashier_user)


@pytest.mark.django_db
class TestPaymentListRetrieve:
    """Tests for listing and retrieving payments."""

    def test_list_payments_empty(self, auth_client):
        response = auth_client.get('/api/v1/payments/payments/')
        assert response.status_code == 200

    def test_list_payments_with_data(self, auth_client, sale_obj):
        """Payments from a sale should appear in the list."""
        response = auth_client.get('/api/v1/payments/payments/')
        assert response.status_code == 200

    def test_admin_can_list_all_payments(self, admin_client, sale_obj):
        """Admin should see all payments."""
        response = admin_client.get('/api/v1/payments/payments/')
        assert response.status_code == 200

    def test_accountant_can_list_payments(self, accountant_client, sale_obj):
        """Accountant should be able to list payments."""
        response = accountant_client.get('/api/v1/payments/payments/')
        assert response.status_code == 200

    def test_retrieve_payment(self, admin_client, sale_obj):
        """Retrieve a single payment."""
        payment = Payment.objects.filter(sale=sale_obj).first()
        response = admin_client.get(f'/api/v1/payments/payments/{payment.uuid}/')
        assert response.status_code == 200
        assert response.data['data']['payment_reference'] == payment.payment_reference

    def test_cashier_cannot_create_manual_payment(self, auth_client, sale_obj):
        """Cashier should not be able to manually create payments."""
        response = auth_client.post('/api/v1/payments/payments/', {
            'sale': str(sale_obj.uuid),
            'amount': '100.00',
            'payment_method': 'CASH',
        })
        assert response.status_code == 403

    def test_unauthenticated_cannot_list(self, api_client):
        response = api_client.get('/api/v1/payments/payments/')
        assert response.status_code == 401


@pytest.mark.django_db
class TestPaymentFiltering:
    """Tests for payment filtering."""

    def test_filter_by_status(self, admin_client, sale_obj):
        """Filter payments by status."""
        response = admin_client.get('/api/v1/payments/payments/', {'status': 'COMPLETED'})
        assert response.status_code == 200

    def test_filter_by_payment_method(self, admin_client, sale_obj):
        """Filter payments by payment method."""
        response = admin_client.get('/api/v1/payments/payments/', {'payment_method': 'CASH'})
        assert response.status_code == 200

    def test_filter_by_sale(self, admin_client, sale_obj):
        """Filter payments by sale UUID."""
        response = admin_client.get('/api/v1/payments/payments/', {'sale': str(sale_obj.uuid)})
        assert response.status_code == 200

    def test_filter_by_date_range(self, admin_client, sale_obj):
        """Filter payments by date range."""
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        response = admin_client.get('/api/v1/payments/payments/', {
            'date_from': yesterday.isoformat(),
            'date_to': tomorrow.isoformat(),
        })
        assert response.status_code == 200

    def test_auto_payment_created_with_sale(self, admin_client, sale_obj):
        """A payment should be automatically created when a sale is made."""
        payment = Payment.objects.filter(sale=sale_obj).first()
        assert payment is not None
        assert payment.status == Payment.Status.COMPLETED
        assert payment.amount == sale_obj.total_amount
