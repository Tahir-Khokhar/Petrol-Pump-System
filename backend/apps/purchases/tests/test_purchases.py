import pytest
from decimal import Decimal
from datetime import date

from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.fuel.models import FuelType, Tank
from apps.suppliers.models import Supplier
from apps.purchases.models import Purchase


@pytest.fixture
def super_admin_user(db):
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
def inventory_manager_user(db):
    return User.objects.create_user(
        email='inventory@test.com',
        password='testpass123',
        first_name='Inventory',
        last_name='Manager',
        role=User.Role.INVENTORY_MANAGER,
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
def auth_client(super_admin_user):
    client = APIClient()
    client.force_authenticate(user=super_admin_user)
    return client


@pytest.fixture
def inv_manager_client(inventory_manager_user):
    client = APIClient()
    client.force_authenticate(user=inventory_manager_user)
    return client


@pytest.fixture
def cashier_client(cashier_user):
    client = APIClient()
    client.force_authenticate(user=cashier_user)
    return client


@pytest.fixture
def supplier(db):
    return Supplier.objects.create(
        company_name='Fuel Corp',
        contact_person='John Doe',
        phone='1234567890',
        email='contact@fuelcorp.com',
    )


@pytest.fixture
def fuel_type(db):
    return FuelType.objects.create(
        name='Diesel',
        code='DSL',
        current_price=Decimal('80.00'),
    )


@pytest.fixture
def tank(db, fuel_type):
    return Tank.objects.create(
        tank_number='TANK-001',
        fuel_type=fuel_type,
        capacity=Decimal('10000.00'),
        current_quantity=Decimal('5000.00'),
        minimum_quantity=Decimal('1000.00'),
    )


@pytest.mark.django_db
class TestPurchaseCRUD:
    """Tests for purchase CRUD operations."""

    def test_create_purchase_for_inventory(self, auth_client, supplier):
        data = {
            'supplier': str(supplier.uuid),
            'quantity': '100',
            'price_per_unit': '25.00',
            'purchase_date': str(date.today()),
            'invoice_number': 'INV-001',
        }
        response = auth_client.post('/api/v1/purchases/purchases/', data, format='json')
        assert response.status_code == 201
        assert response.data['success'] is True
        assert response.data['data']['total_cost'] == '2500.00'
        assert Purchase.objects.filter(purchase_number=response.data['data']['purchase_number']).exists()

    def test_create_purchase_fuel_tank_increases_stock(self, auth_client, supplier, fuel_type, tank):
        tank.current_quantity = Decimal('5000.00')
        tank.save()
        data = {
            'supplier': str(supplier.uuid),
            'fuel_type': str(fuel_type.uuid),
            'tank': str(tank.uuid),
            'quantity': '2000.00',
            'price_per_unit': '70.00',
            'purchase_date': str(date.today()),
        }
        response = auth_client.post('/api/v1/purchases/purchases/', data, format='json')
        assert response.status_code == 201
        tank.refresh_from_db()
        assert tank.current_quantity == Decimal('7000.00')

    def test_purchase_total_cost_calculation(self, auth_client, supplier):
        data = {
            'supplier': str(supplier.uuid),
            'quantity': '50',
            'price_per_unit': '35.50',
            'purchase_date': str(date.today()),
        }
        response = auth_client.post('/api/v1/purchases/purchases/', data, format='json')
        assert response.status_code == 201
        assert response.data['data']['total_cost'] == '1775.00'

    def test_list_purchases(self, auth_client, supplier):
        # Create a purchase first
        data = {
            'supplier': str(supplier.uuid),
            'quantity': '10',
            'price_per_unit': '50.00',
            'purchase_date': str(date.today()),
        }
        auth_client.post('/api/v1/purchases/purchases/', data, format='json')

        response = auth_client.get('/api/v1/purchases/purchases/', format='json')
        assert response.status_code == 200
        assert response.data['success'] is True
        assert len(response.data['data']) >= 1

    def test_retrieve_purchase(self, auth_client, supplier):
        data = {
            'supplier': str(supplier.uuid),
            'quantity': '10',
            'price_per_unit': '50.00',
            'purchase_date': str(date.today()),
        }
        create_resp = auth_client.post('/api/v1/purchases/purchases/', data, format='json')
        purchase_uuid = create_resp.data['data']['uuid']

        response = auth_client.get(f'/api/v1/purchases/purchases/{purchase_uuid}/', format='json')
        assert response.status_code == 200
        assert response.data['data']['uuid'] == purchase_uuid

    def test_cashier_cannot_create_purchase(self, cashier_client, supplier):
        data = {
            'supplier': str(supplier.uuid),
            'quantity': '10',
            'price_per_unit': '50.00',
            'purchase_date': str(date.today()),
        }
        response = cashier_client.post('/api/v1/purchases/purchases/', data, format='json')
        assert response.status_code == 403

    def test_quantity_must_be_positive(self, auth_client, supplier):
        data = {
            'supplier': str(supplier.uuid),
            'quantity': '-5',
            'price_per_unit': '50.00',
            'purchase_date': str(date.today()),
        }
        response = auth_client.post('/api/v1/purchases/purchases/', data, format='json')
        assert response.status_code == 400

    def test_purchase_search_by_purchase_number(self, auth_client, supplier):
        data = {
            'supplier': str(supplier.uuid),
            'quantity': '10',
            'price_per_unit': '50.00',
            'purchase_date': str(date.today()),
        }
        create_resp = auth_client.post('/api/v1/purchases/purchases/', data, format='json')
        purchase_number = create_resp.data['data']['purchase_number']

        response = auth_client.get(f'/api/v1/purchases/purchases/?search={purchase_number}', format='json')
        assert response.status_code == 200
        assert len(response.data['data']) >= 1
