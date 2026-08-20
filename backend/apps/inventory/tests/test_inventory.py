import pytest
from decimal import Decimal

from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.inventory.models import InventoryItem, InventoryTransaction


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
def inventory_item(db):
    return InventoryItem.objects.create(
        name='Engine Oil 5W-30',
        sku='EO-5W30-001',
        category=InventoryItem.Category.ENGINE_OIL,
        description='Synthetic engine oil',
        unit='Liter',
        current_stock=Decimal('50.00'),
        minimum_stock_level=Decimal('10.00'),
        cost_price=Decimal('25.00'),
        selling_price=Decimal('35.00'),
    )


@pytest.mark.django_db
class TestInventoryItemCRUD:
    """Tests for inventory item CRUD operations."""

    def test_create_inventory_item(self, auth_client):
        data = {
            'name': 'Brake Fluid',
            'sku': 'BF-001',
            'category': 'LUBRICANT',
            'unit': 'Bottle',
            'cost_price': '15.00',
            'selling_price': '22.00',
        }
        response = auth_client.post('/api/v1/inventory/items/', data, format='json')
        assert response.status_code == 201
        assert response.data['success'] is True
        assert response.data['data']['name'] == 'Brake Fluid'
        assert response.data['data']['sku'] == 'BF-001'
        assert InventoryItem.objects.filter(sku='BF-001').exists()

    def test_create_inventory_item_duplicate_sku(self, auth_client, inventory_item):
        data = {
            'name': 'Duplicate Item',
            'sku': 'EO-5W30-001',
            'category': 'OTHER',
        }
        response = auth_client.post('/api/v1/inventory/items/', data, format='json')
        assert response.status_code == 400

    def test_list_inventory_items(self, auth_client, inventory_item):
        response = auth_client.get('/api/v1/inventory/items/', format='json')
        assert response.status_code == 200
        assert response.data['success'] is True
        assert len(response.data['data']) >= 1

    def test_retrieve_inventory_item(self, auth_client, inventory_item):
        url = f'/api/v1/inventory/items/{inventory_item.uuid}/'
        response = auth_client.get(url, format='json')
        assert response.status_code == 200
        assert response.data['data']['name'] == 'Engine Oil 5W-30'

    def test_update_inventory_item(self, auth_client, inventory_item):
        url = f'/api/v1/inventory/items/{inventory_item.uuid}/'
        data = {'name': 'Updated Engine Oil'}
        response = auth_client.patch(url, data, format='json')
        assert response.status_code == 200
        assert response.data['data']['name'] == 'Updated Engine Oil'

    def test_delete_inventory_item(self, auth_client, inventory_item):
        url = f'/api/v1/inventory/items/{inventory_item.uuid}/'
        response = auth_client.delete(url, format='json')
        assert response.status_code == 200
        assert not InventoryItem.objects.filter(uuid=inventory_item.uuid).exists()

    def test_cashier_cannot_create_item(self, cashier_client):
        data = {'name': 'Test', 'sku': 'TEST-001', 'category': 'OTHER'}
        response = cashier_client.post('/api/v1/inventory/items/', data, format='json')
        assert response.status_code == 403

    def test_cost_price_must_be_positive(self, auth_client):
        data = {
            'name': 'Bad Item',
            'sku': 'BAD-001',
            'category': 'OTHER',
            'cost_price': '-5.00',
        }
        response = auth_client.post('/api/v1/inventory/items/', data, format='json')
        assert response.status_code == 400


@pytest.mark.django_db
class TestStockAdjustment:
    """Tests for stock adjustment operations."""

    def test_stock_in(self, inv_manager_client, inventory_item):
        data = {
            'inventory_item': str(inventory_item.uuid),
            'quantity': '20.00',
            'transaction_type': 'STOCK_IN',
            'notes': 'New stock received',
        }
        response = inv_manager_client.post('/api/v1/inventory/stock-adjust/', data, format='json')
        assert response.status_code == 201
        assert response.data['success'] is True
        inventory_item.refresh_from_db()
        assert inventory_item.current_stock == Decimal('70.00')

    def test_stock_out(self, inv_manager_client, inventory_item):
        data = {
            'inventory_item': str(inventory_item.uuid),
            'quantity': '10.00',
            'transaction_type': 'STOCK_OUT',
        }
        response = inv_manager_client.post('/api/v1/inventory/stock-adjust/', data, format='json')
        assert response.status_code == 201
        inventory_item.refresh_from_db()
        assert inventory_item.current_stock == Decimal('40.00')

    def test_negative_stock_prevention(self, inv_manager_client, inventory_item):
        data = {
            'inventory_item': str(inventory_item.uuid),
            'quantity': '999.00',
            'transaction_type': 'STOCK_OUT',
        }
        response = inv_manager_client.post('/api/v1/inventory/stock-adjust/', data, format='json')
        assert response.status_code == 400
        inventory_item.refresh_from_db()
        assert inventory_item.current_stock == Decimal('50.00')

    def test_damaged_reduction(self, inv_manager_client, inventory_item):
        data = {
            'inventory_item': str(inventory_item.uuid),
            'quantity': '5.00',
            'transaction_type': 'DAMAGED',
            'notes': 'Damaged in transit',
        }
        response = inv_manager_client.post('/api/v1/inventory/stock-adjust/', data, format='json')
        assert response.status_code == 201
        inventory_item.refresh_from_db()
        assert inventory_item.current_stock == Decimal('45.00')

    def test_adjustment_creates_transaction_record(self, inv_manager_client, inventory_item):
        data = {
            'inventory_item': str(inventory_item.uuid),
            'quantity': '10.00',
            'transaction_type': 'RETURN',
        }
        response = inv_manager_client.post('/api/v1/inventory/stock-adjust/', data, format='json')
        assert response.status_code == 201
        txn_uuid = response.data['data']['uuid']
        txn = InventoryTransaction.objects.get(uuid=txn_uuid)
        assert txn.previous_stock == Decimal('50.00')
        assert txn.new_stock == Decimal('60.00')

    def test_cashier_cannot_adjust_stock(self, cashier_client, inventory_item):
        data = {
            'inventory_item': str(inventory_item.uuid),
            'quantity': '10.00',
            'transaction_type': 'STOCK_IN',
        }
        response = cashier_client.post('/api/v1/inventory/stock-adjust/', data, format='json')
        assert response.status_code == 403


@pytest.mark.django_db
class TestLowStockDetection:
    """Tests for low stock detection."""

    def test_low_stock_endpoint(self, auth_client, inventory_item):
        # Set current stock equal to minimum to trigger low stock
        inventory_item.current_stock = Decimal('5.00')
        inventory_item.minimum_stock_level = Decimal('10.00')
        inventory_item.save()

        response = auth_client.get('/api/v1/inventory/low-stock/', format='json')
        assert response.status_code == 200
        assert response.data['success'] is True
        uuids = [item['uuid'] for item in response.data['data']]
        assert str(inventory_item.uuid) in uuids

    def test_low_stock_filter(self, auth_client, inventory_item):
        inventory_item.current_stock = Decimal('5.00')
        inventory_item.minimum_stock_level = Decimal('10.00')
        inventory_item.save()

        response = auth_client.get('/api/v1/inventory/items/?is_low_stock=true', format='json')
        assert response.status_code == 200
        uuids = [item['uuid'] for item in response.data['data']]
        assert str(inventory_item.uuid) in uuids

    def test_item_not_low_stock(self, auth_client, inventory_item):
        inventory_item.current_stock = Decimal('100.00')
        inventory_item.minimum_stock_level = Decimal('10.00')
        inventory_item.save()

        response = auth_client.get('/api/v1/inventory/low-stock/', format='json')
        uuids = [item['uuid'] for item in response.data['data']]
        assert str(inventory_item.uuid) not in uuids
