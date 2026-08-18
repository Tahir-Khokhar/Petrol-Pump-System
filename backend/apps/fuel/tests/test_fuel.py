import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.fuel.models import FuelType, FuelPriceHistory, Tank


# --- Fixtures ---


@pytest.fixture
def super_admin():
    return User.objects.create_superuser(
        email='admin@petropump.com',
        password='AdminPass123',
        first_name='System',
        last_name='Administrator',
    )


@pytest.fixture
def pump_manager():
    user = User.objects.create_user(
        email='manager@petropump.com',
        password='ManagerPass123',
        first_name='Pump',
        last_name='Manager',
        role=User.Role.PUMP_MANAGER,
    )
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def inventory_manager():
    user = User.objects.create_user(
        email='inventory@petropump.com',
        password='InventoryPass123',
        first_name='Inventory',
        last_name='Manager',
        role=User.Role.INVENTORY_MANAGER,
    )
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def cashier():
    user = User.objects.create_user(
        email='cashier@petropump.com',
        password='CashierPass123',
        first_name='John',
        last_name='Doe',
        role=User.Role.CASHIER,
    )
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def fuel_type():
    return FuelType.objects.create(
        name='Petrol',
        code='PETROL',
        description='Regular petrol',
        current_price=Decimal('85.50'),
        minimum_stock_level=Decimal('500.00'),
    )


@pytest.fixture
def fuel_type_diesel():
    return FuelType.objects.create(
        name='Diesel',
        code='DIESEL',
        description='High-speed diesel',
        current_price=Decimal('75.00'),
        minimum_stock_level=Decimal('1000.00'),
    )


@pytest.fixture
def tank(fuel_type):
    return Tank.objects.create(
        tank_number='TANK-001',
        fuel_type=fuel_type,
        capacity=Decimal('10000.00'),
        current_quantity=Decimal('5000.00'),
        minimum_quantity=Decimal('500.00'),
        location='Underground - Bay 1',
    )


@pytest.fixture
def auth_client(api_client, super_admin):
    refresh = RefreshToken.for_user(super_admin)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def manager_auth_client(api_client, pump_manager):
    refresh = RefreshToken.for_user(pump_manager)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def cashier_auth_client(api_client, cashier):
    refresh = RefreshToken.for_user(cashier)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def inventory_auth_client(api_client, inventory_manager):
    refresh = RefreshToken.for_user(inventory_manager)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


# --- Fuel Type Tests ---


@pytest.mark.django_db
class TestCreateFuelType:
    """Tests for creating fuel types."""

    def test_create_fuel_type_success(self, auth_client):
        """SUPER_ADMIN can create a fuel type."""
        url = reverse('fuel-type-list')
        data = {
            'name': 'Premium Petrol',
            'code': 'PREM_PETROL',
            'description': 'High octane petrol',
            'current_price': '95.00',
            'minimum_stock_level': '200.00',
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['data']['name'] == 'Premium Petrol'
        assert response.data['data']['code'] == 'PREM_PETROL'
        assert response.data['data']['current_price'] == '95.00'
        assert FuelType.objects.count() == 1

    def test_create_fuel_type_duplicate_name(self, auth_client, fuel_type):
        """Creating a fuel type with duplicate name fails."""
        url = reverse('fuel-type-list')
        data = {
            'name': 'Petrol',
            'code': 'PETROL2',
            'current_price': '90.00',
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    def test_create_fuel_type_duplicate_code(self, auth_client, fuel_type):
        """Creating a fuel type with duplicate code fails."""
        url = reverse('fuel-type-list')
        data = {
            'name': 'Petrol Plus',
            'code': 'PETROL',
            'current_price': '90.00',
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    def test_create_fuel_type_manager_allowed(self, manager_auth_client):
        """PUMP_MANAGER can create fuel types."""
        url = reverse('fuel-type-list')
        data = {
            'name': 'CNG',
            'code': 'CNG',
            'current_price': '70.00',
        }
        response = manager_auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True

    def test_create_fuel_type_cashier_forbidden(self, cashier_auth_client):
        """CASHIER cannot create fuel types."""
        url = reverse('fuel-type-list')
        data = {
            'name': 'CNG',
            'code': 'CNG',
            'current_price': '70.00',
        }
        response = cashier_auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['success'] is False


@pytest.mark.django_db
class TestListFuelTypes:
    """Tests for listing fuel types."""

    def test_list_fuel_types_empty(self, auth_client):
        """Listing fuel types when none exist returns empty list."""
        url = reverse('fuel-type-list')
        response = auth_client.get(url, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']) == 0

    def test_list_fuel_types(self, auth_client, fuel_type, fuel_type_diesel):
        """Listing fuel types returns all types."""
        url = reverse('fuel-type-list')
        response = auth_client.get(url, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']) == 2

    def test_list_fuel_types_excludes_description(self, auth_client, fuel_type):
        """List view excludes the description field."""
        url = reverse('fuel-type-list')
        response = auth_client.get(url, format='json')

        assert response.status_code == status.HTTP_200_OK
        for item in response.data['data']:
            assert 'description' not in item

    def test_list_fuel_types_filter_active(self, auth_client, fuel_type):
        """Filtering by is_active works."""
        fuel_type.is_active = False
        fuel_type.save()

        url = reverse('fuel-type-list')
        response = auth_client.get(url, {'is_active': 'true'}, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 0

    def test_list_fuel_types_search(self, auth_client, fuel_type, fuel_type_diesel):
        """Search by name works."""
        url = reverse('fuel-type-list')
        response = auth_client.get(url, {'search': 'Petrol'}, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['name'] == 'Petrol'


@pytest.mark.django_db
class TestRetrieveFuelType:
    """Tests for retrieving a single fuel type."""

    def test_retrieve_fuel_type(self, auth_client, fuel_type):
        """Retrieve a fuel type by UUID."""
        url = reverse('fuel-type-detail', kwargs={'uuid': fuel_type.uuid})
        response = auth_client.get(url, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['uuid'] == str(fuel_type.uuid)
        assert response.data['data']['name'] == 'Petrol'
        assert response.data['data']['code'] == 'PETROL'
        # Detail view includes description
        assert 'description' in response.data['data']


# --- Price Update Tests ---


@pytest.mark.django_db
class TestUpdatePrice:
    """Tests for updating fuel prices."""

    def test_update_price_success(self, auth_client, fuel_type):
        """SUPER_ADMIN can update fuel price."""
        url = reverse('fuel-price-update')
        data = {
            'fuel_type': str(fuel_type.uuid),
            'new_price': '90.00',
            'reason': 'Market rate increase',
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['current_price'] == '90.00'

        # Verify price updated in DB
        fuel_type.refresh_from_db()
        assert fuel_type.current_price == Decimal('90.00')

    def test_update_price_creates_history(self, auth_client, fuel_type):
        """Price update creates a history record."""
        url = reverse('fuel-price-update')
        data = {
            'fuel_type': str(fuel_type.uuid),
            'new_price': '92.00',
            'reason': 'Seasonal adjustment',
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert FuelPriceHistory.objects.count() == 1

        history = FuelPriceHistory.objects.first()
        assert history.previous_price == Decimal('85.50')
        assert history.new_price == Decimal('92.00')
        assert history.reason == 'Seasonal adjustment'
        assert history.changed_by == User.objects.get(email='admin@petropump.com')

    def test_update_price_zero_rejected(self, auth_client, fuel_type):
        """Price update with zero is rejected."""
        url = reverse('fuel-price-update')
        data = {
            'fuel_type': str(fuel_type.uuid),
            'new_price': '0.00',
            'reason': 'Test',
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    def test_update_price_negative_rejected(self, auth_client, fuel_type):
        """Price update with negative value is rejected."""
        url = reverse('fuel-price-update')
        data = {
            'fuel_type': str(fuel_type.uuid),
            'new_price': '-10.00',
            'reason': 'Test',
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    def test_update_price_invalid_fuel_type(self, auth_client):
        """Price update with non-existent fuel type fails."""
        url = reverse('fuel-price-update')
        data = {
            'fuel_type': '00000000-0000-0000-0000-000000000000',
            'new_price': '90.00',
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    def test_update_price_manager_allowed(self, manager_auth_client, fuel_type):
        """PUMP_MANAGER can update fuel price."""
        url = reverse('fuel-price-update')
        data = {
            'fuel_type': str(fuel_type.uuid),
            'new_price': '88.00',
            'reason': 'Daily adjustment',
        }
        response = manager_auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

    def test_update_price_cashier_forbidden(self, cashier_auth_client, fuel_type):
        """CASHIER cannot update fuel price."""
        url = reverse('fuel-price-update')
        data = {
            'fuel_type': str(fuel_type.uuid),
            'new_price': '88.00',
            'reason': 'Test',
        }
        response = cashier_auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['success'] is False


# --- Tank Tests ---


@pytest.mark.django_db
class TestCreateTank:
    """Tests for creating tanks."""

    def test_create_tank_success(self, auth_client, fuel_type):
        """SUPER_ADMIN can create a tank."""
        url = reverse('tank-list')
        data = {
            'tank_number': 'TANK-002',
            'fuel_type': str(fuel_type.uuid),
            'capacity': '20000.00',
            'current_quantity': '10000.00',
            'minimum_quantity': '1000.00',
            'location': 'Underground - Bay 2',
            'status': 'ACTIVE',
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['data']['tank_number'] == 'TANK-002'
        assert response.data['data']['fuel_type_name'] == 'Petrol'
        assert Tank.objects.count() == 1

    def test_create_tank_inventory_manager_allowed(self, inventory_auth_client, fuel_type):
        """INVENTORY_MANAGER can create tanks."""
        url = reverse('tank-list')
        data = {
            'tank_number': 'TANK-003',
            'fuel_type': str(fuel_type.uuid),
            'capacity': '15000.00',
            'current_quantity': '0',
        }
        response = inventory_auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True

    def test_create_tank_duplicate_number(self, auth_client, tank):
        """Creating tank with duplicate number fails."""
        url = reverse('tank-list')
        data = {
            'tank_number': 'TANK-001',
            'fuel_type': str(tank.fuel_type.uuid),
            'capacity': '5000.00',
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False


@pytest.mark.django_db
class TestTankStockAdjustment:
    """Tests for tank stock adjustment."""

    def test_adjust_stock_add(self, auth_client, tank):
        """Adding stock to a tank succeeds."""
        url = reverse('tank-stock-adjustment')
        data = {
            'tank': str(tank.uuid),
            'adjustment_quantity': '2000.00',
            'reason': 'Delivery received',
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['current_quantity'] == '7000.00'

        tank.refresh_from_db()
        assert tank.current_quantity == Decimal('7000.00')

    def test_adjust_stock_remove(self, auth_client, tank):
        """Removing stock from a tank succeeds."""
        url = reverse('tank-stock-adjustment')
        data = {
            'tank': str(tank.uuid),
            'adjustment_quantity': '-1000.00',
            'reason': 'Sale withdrawal',
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['current_quantity'] == '4000.00'

        tank.refresh_from_db()
        assert tank.current_quantity == Decimal('4000.00')

    def test_adjust_stock_zero_rejected(self, auth_client, tank):
        """Zero adjustment is rejected."""
        url = reverse('tank-stock-adjustment')
        data = {
            'tank': str(tank.uuid),
            'adjustment_quantity': '0.00',
            'reason': 'Test',
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    def test_adjust_stock_negative_stock_prevented(self, auth_client, tank):
        """Adjustment that would result in negative stock is prevented."""
        url = reverse('tank-stock-adjustment')
        data = {
            'tank': str(tank.uuid),
            'adjustment_quantity': '-6000.00',
            'reason': 'Excess removal',
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

        tank.refresh_from_db()
        assert tank.current_quantity == Decimal('5000.00')

    def test_adjust_stock_exceeding_capacity_prevented(self, auth_client, tank):
        """Adjustment that would exceed capacity is prevented."""
        url = reverse('tank-stock-adjustment')
        data = {
            'tank': str(tank.uuid),
            'adjustment_quantity': '6000.00',
            'reason': 'Overfill attempt',
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

        tank.refresh_from_db()
        assert tank.current_quantity == Decimal('5000.00')

    def test_adjust_stock_invalid_tank(self, auth_client):
        """Adjustment with non-existent tank fails."""
        url = reverse('tank-stock-adjustment')
        data = {
            'tank': '00000000-0000-0000-0000-000000000000',
            'adjustment_quantity': '100.00',
            'reason': 'Test',
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    def test_adjust_stock_cashier_forbidden(self, cashier_auth_client, tank):
        """CASHIER cannot adjust tank stock."""
        url = reverse('tank-stock-adjustment')
        data = {
            'tank': str(tank.uuid),
            'adjustment_quantity': '100.00',
            'reason': 'Test',
        }
        response = cashier_auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['success'] is False
