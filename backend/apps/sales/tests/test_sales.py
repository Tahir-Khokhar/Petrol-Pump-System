import pytest
from decimal import Decimal

from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.customers.models import Customer
from apps.fuel.models import FuelType, Tank
from apps.pumps.models import Nozzle, Pump
from apps.sales.models import Refund, Sale


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
def customer(db):
    return Customer.objects.create(
        full_name='John Doe',
        phone='1234567890',
        is_corporate=False,
        credit_limit=Decimal('0'),
        outstanding_balance=Decimal('0'),
    )


@pytest.fixture
def corporate_customer(db):
    return Customer.objects.create(
        full_name='Corp Inc',
        phone='9876543210',
        is_corporate=True,
        company_name='Corp Inc',
        credit_limit=Decimal('50000'),
        outstanding_balance=Decimal('0'),
    )


@pytest.fixture
def cashier_user(db):
    user = User.objects.create_user(
        email='cashier@test.com',
        password='testpass123',
        first_name='Cash',
        last_name='ier',
        role=User.Role.CASHIER,
    )
    return user


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        email='admin@test.com',
        password='testpass123',
        first_name='Super',
        last_name='Admin',
        role=User.Role.SUPER_ADMIN,
        is_staff=True,
        is_superuser=True,
    )
    return user


@pytest.fixture
def manager_user(db):
    user = User.objects.create_user(
        email='manager@test.com',
        password='testpass123',
        first_name='Pump',
        last_name='Manager',
        role=User.Role.PUMP_MANAGER,
    )
    return user


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
def manager_client(api_client, manager_user):
    token = RefreshToken.for_user(manager_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return api_client


# =============================================================================
# Sale Tests
# =============================================================================

@pytest.mark.django_db
class TestCreateSale:
    """Tests for the sale creation endpoint."""

    def test_successful_sale(self, auth_client, pump, nozzle, fuel_type, tank):
        """A successful sale should reduce tank stock and increase nozzle meter."""
        initial_tank_qty = tank.current_quantity
        initial_meter = nozzle.current_meter_reading

        response = auth_client.post('/api/v1/sales/create-sale/', {
            'pump': str(pump.uuid),
            'nozzle': str(nozzle.uuid),
            'quantity': '10.00',
            'payment_method': 'CASH',
        })

        assert response.status_code == 201
        data = response.data['data']
        assert data['receipt_number']
        assert float(data['total_amount']) == float(Decimal('10.00') * fuel_type.current_price)
        assert data['status'] == 'COMPLETED'

        # Verify tank stock decreased
        tank.refresh_from_db()
        assert tank.current_quantity == initial_tank_qty - Decimal('10.00')

        # Verify nozzle meter increased
        nozzle.refresh_from_db()
        assert nozzle.current_meter_reading == initial_meter + Decimal('10.00')

    def test_successful_sale_with_customer(self, auth_client, pump, nozzle, customer):
        """A sale with a customer should be recorded correctly."""
        response = auth_client.post('/api/v1/sales/create-sale/', {
            'pump': str(pump.uuid),
            'nozzle': str(nozzle.uuid),
            'customer': str(customer.uuid),
            'quantity': '5.00',
            'payment_method': 'CASH',
        })

        assert response.status_code == 201
        data = response.data['data']
        assert data['customer']['id'] == str(customer.uuid)

    def test_sale_with_discount(self, auth_client, pump, nozzle):
        """A sale with a discount should have the correct total."""
        response = auth_client.post('/api/v1/sales/create-sale/', {
            'pump': str(pump.uuid),
            'nozzle': str(nozzle.uuid),
            'quantity': '10.00',
            'discount': '50.00',
            'payment_method': 'CASH',
        })

        assert response.status_code == 201
        data = response.data['data']
        subtotal = Decimal('10.00') * nozzle.fuel_type.current_price
        assert float(data['subtotal']) == float(subtotal)
        assert float(data['discount']) == 50.00
        assert float(data['total_amount']) == float(subtotal - Decimal('50.00'))

    def test_insufficient_stock(self, auth_client, pump, nozzle, tank):
        """A sale exceeding available stock should be rejected."""
        tank.current_quantity = Decimal('5.00')
        tank.save()

        response = auth_client.post('/api/v1/sales/create-sale/', {
            'pump': str(pump.uuid),
            'nozzle': str(nozzle.uuid),
            'quantity': '10.00',
            'payment_method': 'CASH',
        })

        assert response.status_code == 400
        assert 'Insufficient stock' in str(response.data)

    def test_inactive_pump_rejected(self, auth_client, pump, nozzle):
        """A sale on an inactive pump should be rejected."""
        pump.status = Pump.Status.INACTIVE
        pump.save()

        response = auth_client.post('/api/v1/sales/create-sale/', {
            'pump': str(pump.uuid),
            'nozzle': str(nozzle.uuid),
            'quantity': '10.00',
            'payment_method': 'CASH',
        })

        assert response.status_code == 400
        assert 'not active' in str(response.data).lower()

    def test_inactive_nozzle_rejected(self, auth_client, pump, nozzle):
        """A sale on an inactive nozzle should be rejected."""
        nozzle.status = Nozzle.Status.INACTIVE
        nozzle.save()

        response = auth_client.post('/api/v1/sales/create-sale/', {
            'pump': str(pump.uuid),
            'nozzle': str(nozzle.uuid),
            'quantity': '10.00',
            'payment_method': 'CASH',
        })

        assert response.status_code == 400
        assert 'not active' in str(response.data).lower()

    def test_invalid_quantity_zero(self, auth_client, pump, nozzle):
        """A sale with zero quantity should be rejected."""
        response = auth_client.post('/api/v1/sales/create-sale/', {
            'pump': str(pump.uuid),
            'nozzle': str(nozzle.uuid),
            'quantity': '0',
            'payment_method': 'CASH',
        })

        assert response.status_code == 400

    def test_invalid_quantity_negative(self, auth_client, pump, nozzle):
        """A sale with negative quantity should be rejected."""
        response = auth_client.post('/api/v1/sales/create-sale/', {
            'pump': str(pump.uuid),
            'nozzle': str(nozzle.uuid),
            'quantity': '-5.00',
            'payment_method': 'CASH',
        })

        assert response.status_code == 400

    def test_nozzle_not_belonging_to_pump(self, auth_client, pump, nozzle, fuel_type, db):
        """A nozzle that doesn't belong to the pump should be rejected."""
        other_pump = Pump.objects.create(
            pump_number='PMP-002',
            name='Pump 2',
            status=Pump.Status.ACTIVE,
        )

        response = auth_client.post('/api/v1/sales/create-sale/', {
            'pump': str(other_pump.uuid),
            'nozzle': str(nozzle.uuid),
            'quantity': '10.00',
            'payment_method': 'CASH',
        })

        assert response.status_code == 400
        assert 'not belong' in str(response.data).lower()

    def test_unauthenticated_cannot_create(self, api_client, pump, nozzle):
        """Unauthenticated users cannot create sales."""
        response = api_client.post('/api/v1/sales/create-sale/', {
            'pump': str(pump.uuid),
            'nozzle': str(nozzle.uuid),
            'quantity': '10.00',
            'payment_method': 'CASH',
        })

        assert response.status_code == 401

    def test_corporate_credit_limit_check(self, auth_client, pump, nozzle, corporate_customer):
        """A corporate customer exceeding credit limit should be rejected."""
        corporate_customer.outstanding_balance = Decimal('49000')
        corporate_customer.save()

        response = auth_client.post('/api/v1/sales/create-sale/', {
            'pump': str(pump.uuid),
            'nozzle': str(nozzle.uuid),
            'customer': str(corporate_customer.uuid),
            'quantity': '100.00',
            'payment_method': 'CREDIT',
        })

        # 100 * 85.50 = 8550, 49000 + 8550 = 57550 > 50000
        assert response.status_code == 400
        assert 'credit limit' in str(response.data).lower()

    def test_corporate_within_credit_limit(self, auth_client, pump, nozzle, corporate_customer):
        """A corporate customer within credit limit should succeed."""
        response = auth_client.post('/api/v1/sales/create-sale/', {
            'pump': str(pump.uuid),
            'nozzle': str(nozzle.uuid),
            'customer': str(corporate_customer.uuid),
            'quantity': '10.00',
            'payment_method': 'CREDIT',
        })

        assert response.status_code == 201
        # Check outstanding balance increased
        corporate_customer.refresh_from_db()
        assert corporate_customer.outstanding_balance > 0


@pytest.mark.django_db
class TestListRetrieveSales:
    """Tests for listing and retrieving sales."""

    def test_list_sales_empty(self, auth_client):
        """Empty list should return success with empty data."""
        response = auth_client.get('/api/v1/sales/sales/')
        assert response.status_code == 200

    def test_cashier_sees_own_sales(self, auth_client, pump, nozzle, cashier_user):
        """Cashier should only see their own sales."""
        # Create a sale as this cashier
        from apps.sales.services import create_sale
        create_sale({
            'pump': pump.uuid,
            'nozzle': nozzle.uuid,
            'quantity': Decimal('10.00'),
            'discount': Decimal('0'),
            'payment_method': 'CASH',
            'notes': '',
        }, cashier_user)

        # Create another cashier and a sale for them
        other_cashier = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            first_name='Other',
            last_name='Cashier',
            role=User.Role.CASHIER,
        )
        create_sale({
            'pump': pump.uuid,
            'nozzle': nozzle.uuid,
            'quantity': Decimal('5.00'),
            'discount': Decimal('0'),
            'payment_method': 'CASH',
            'notes': '',
        }, other_cashier)

        response = auth_client.get('/api/v1/sales/sales/')
        assert response.status_code == 200
        results = response.data['data']['results'] if 'results' in response.data['data'] else response.data['data']
        # Cashier should only see their own sale
        for sale in results:
            assert sale['employee']['id'] == str(cashier_user.uuid)

    def test_admin_sees_all_sales(self, admin_client, pump, nozzle, cashier_user):
        """Admin should see all sales."""
        from apps.sales.services import create_sale
        create_sale({
            'pump': pump.uuid,
            'nozzle': nozzle.uuid,
            'quantity': Decimal('10.00'),
            'discount': Decimal('0'),
            'payment_method': 'CASH',
            'notes': '',
        }, cashier_user)

        response = admin_client.get('/api/v1/sales/sales/')
        assert response.status_code == 200

    def test_get_receipt(self, auth_client, pump, nozzle, cashier_user):
        """Get receipt for a sale."""
        from apps.sales.services import create_sale
        sale = create_sale({
            'pump': pump.uuid,
            'nozzle': nozzle.uuid,
            'quantity': Decimal('10.00'),
            'discount': Decimal('0'),
            'payment_method': 'CASH',
            'notes': '',
        }, cashier_user)

        response = auth_client.get(f'/api/v1/sales/{sale.uuid}/receipt/')
        assert response.status_code == 200
        assert response.data['data']['receipt_number'] == sale.receipt_number


@pytest.mark.django_db
class TestRefund:
    """Tests for the refund functionality."""

    def _create_test_sale(self, pump, nozzle, cashier_user):
        from apps.sales.services import create_sale
        return create_sale({
            'pump': pump.uuid,
            'nozzle': nozzle.uuid,
            'quantity': Decimal('10.00'),
            'discount': Decimal('0'),
            'payment_method': 'CASH',
            'notes': '',
        }, cashier_user)

    def test_create_refund_as_admin(self, admin_client, pump, nozzle, cashier_user):
        """SUPER_ADMIN can create a refund, auto-approved."""
        sale = self._create_test_sale(pump, nozzle, cashier_user)

        response = admin_client.post('/api/v1/sales/refunds/', {
            'sale': str(sale.uuid),
            'amount': str(sale.total_amount / 2),
            'reason': 'Customer complaint',
        })

        assert response.status_code == 201
        data = response.data['data']
        assert data['status'] == 'APPROVED'  # Auto-approved for SUPER_ADMIN
        assert data['processed_at'] is not None

    def test_create_refund_as_manager(self, manager_client, pump, nozzle, cashier_user):
        """PUMP_MANAGER can create a refund, status PENDING."""
        sale = self._create_test_sale(pump, nozzle, cashier_user)

        response = manager_client.post('/api/v1/sales/refunds/', {
            'sale': str(sale.uuid),
            'amount': '100.00',
            'reason': 'Overcharged',
        })

        assert response.status_code == 201
        data = response.data['data']
        assert data['status'] == 'PENDING'

    def test_refund_amount_validation_exceeds_total(self, admin_client, pump, nozzle, cashier_user):
        """Refund amount exceeding sale total should be rejected."""
        sale = self._create_test_sale(pump, nozzle, cashier_user)

        response = admin_client.post('/api/v1/sales/refunds/', {
            'sale': str(sale.uuid),
            'amount': str(sale.total_amount + Decimal('1.00')),
            'reason': 'Testing',
        })

        assert response.status_code == 400
        assert 'exceeds' in str(response.data).lower()

    def test_refund_zero_amount_rejected(self, admin_client, pump, nozzle, cashier_user):
        """Refund with zero amount should be rejected."""
        sale = self._create_test_sale(pump, nozzle, cashier_user)

        response = admin_client.post('/api/v1/sales/refunds/', {
            'sale': str(sale.uuid),
            'amount': '0',
            'reason': 'Testing',
        })

        assert response.status_code == 400

    def test_refund_negative_amount_rejected(self, admin_client, pump, nozzle, cashier_user):
        """Refund with negative amount should be rejected."""
        sale = self._create_test_sale(pump, nozzle, cashier_user)

        response = admin_client.post('/api/v1/sales/refunds/', {
            'sale': str(sale.uuid),
            'amount': '-50.00',
            'reason': 'Testing',
        })

        assert response.status_code == 400

    def test_cashier_cannot_create_refund(self, auth_client, pump, nozzle, cashier_user):
        """CASHIER should not be able to create refunds."""
        sale = self._create_test_sale(pump, nozzle, cashier_user)

        response = auth_client.post('/api/v1/sales/refunds/', {
            'sale': str(sale.uuid),
            'amount': '100.00',
            'reason': 'Testing',
        })

        assert response.status_code == 403

    def test_refund_on_non_completed_sale(self, admin_client, pump, nozzle, cashier_user):
        """Refund on a cancelled sale should be rejected."""
        sale = self._create_test_sale(pump, nozzle, cashier_user)
        sale.status = Sale.Status.CANCELLED
        sale.save()

        response = admin_client.post('/api/v1/sales/refunds/', {
            'sale': str(sale.uuid),
            'amount': '100.00',
            'reason': 'Testing',
        })

        assert response.status_code == 400
        assert 'completed' in str(response.data).lower()

    def test_refund_reverses_corporate_balance(self, admin_client, pump, nozzle, cashier_user, corporate_customer):
        """Refund should reverse corporate customer outstanding balance."""
        from apps.sales.services import create_sale
        sale = create_sale({
            'pump': pump.uuid,
            'nozzle': nozzle.uuid,
            'customer': corporate_customer.uuid,
            'quantity': Decimal('10.00'),
            'discount': Decimal('0'),
            'payment_method': 'CREDIT',
            'notes': '',
        }, cashier_user)

        corporate_customer.refresh_from_db()
        balance_after_sale = corporate_customer.outstanding_balance

        # Create full refund (auto-approved for admin)
        response = admin_client.post('/api/v1/sales/refunds/', {
            'sale': str(sale.uuid),
            'amount': str(sale.total_amount),
            'reason': 'Corporate credit reversal',
        })

        assert response.status_code == 201
        corporate_customer.refresh_from_db()
        assert corporate_customer.outstanding_balance < balance_after_sale

    def test_partial_refund_remaining_amount(self, admin_client, pump, nozzle, cashier_user):
        """Partial refund should track remaining refundable amount."""
        sale = self._create_test_sale(pump, nozzle, cashier_user)

        # First partial refund
        half = sale.total_amount / 2
        response = admin_client.post('/api/v1/sales/refunds/', {
            'sale': str(sale.uuid),
            'amount': str(half),
            'reason': 'First partial',
        })
        assert response.status_code == 201

        # Second refund of remaining amount should work
        response2 = admin_client.post('/api/v1/sales/refunds/', {
            'sale': str(sale.uuid),
            'amount': str(half + Decimal('0.01')),
            'reason': 'Second partial',
        })
        assert response2.status_code == 400  # exceeds by 0.01

        # Exact remaining should work
        response3 = admin_client.post('/api/v1/sales/refunds/', {
            'sale': str(sale.uuid),
            'amount': str(half),
            'reason': 'Second partial exact',
        })
        assert response3.status_code == 201

    def test_duplicate_sale_prevention(self, auth_client, pump, nozzle):
        """Each sale should get a unique receipt number."""
        response1 = auth_client.post('/api/v1/sales/create-sale/', {
            'pump': str(pump.uuid),
            'nozzle': str(nozzle.uuid),
            'quantity': '10.00',
            'payment_method': 'CASH',
        })
        response2 = auth_client.post('/api/v1/sales/create-sale/', {
            'pump': str(pump.uuid),
            'nozzle': str(nozzle.uuid),
            'quantity': '5.00',
            'payment_method': 'CASH',
        })

        assert response1.status_code == 201
        assert response2.status_code == 201
        assert response1.data['data']['receipt_number'] != response2.data['data']['receipt_number']
