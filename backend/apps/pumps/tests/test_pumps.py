import pytest
from decimal import Decimal

from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.fuel.models import FuelType, Tank
from apps.pumps.models import Nozzle, Pump


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
def pump_attendant():
    user = User.objects.create_user(
        email='attendant@petropump.com',
        password='AttendantPass123',
        first_name='John',
        last_name='Attendant',
        role=User.Role.PUMP_ATTENDANT,
    )
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def cashier():
    user = User.objects.create_user(
        email='cashier@petropump.com',
        password='CashierPass123',
        first_name='Jane',
        last_name='Cashier',
        role=User.Role.CASHIER,
    )
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def fuel_type_petrol():
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
def tank(fuel_type_petrol):
    return Tank.objects.create(
        tank_number='TANK-001',
        fuel_type=fuel_type_petrol,
        capacity=Decimal('10000.00'),
        current_quantity=Decimal('5000.00'),
        minimum_quantity=Decimal('500.00'),
        location='Underground - Bay 1',
    )


@pytest.fixture
def pump_data(fuel_type_petrol):
    return {
        'pump_number': 'PUMP-001',
        'name': 'Main Pump 1',
        'location': 'Bay 1',
        'status': 'ACTIVE',
        'fuel_type_ids': [str(fuel_type_petrol.uuid)],
    }


@pytest.fixture
def pump(fuel_type_petrol):
    p = Pump.objects.create(
        pump_number='PUMP-001',
        name='Main Pump 1',
        location='Bay 1',
        status='ACTIVE',
    )
    p.fuel_types.add(fuel_type_petrol)
    return p


@pytest.fixture
def nozzle_data(pump, fuel_type_petrol):
    return {
        'nozzle_number': 'NOZ-001',
        'pump_id': str(pump.uuid),
        'fuel_type_id': str(fuel_type_petrol.uuid),
        'opening_meter_reading': '100.00',
        'current_meter_reading': '100.00',
        'status': 'ACTIVE',
    }


@pytest.fixture
def nozzle(pump, fuel_type_petrol):
    return Nozzle.objects.create(
        nozzle_number='NOZ-001',
        pump=pump,
        fuel_type=fuel_type_petrol,
        opening_meter_reading=Decimal('100.00'),
        current_meter_reading=Decimal('100.00'),
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


# --- Pump CRUD Tests ---


@pytest.mark.django_db
class TestPumpCRUD:
    """Tests for pump create, read, update, delete."""

    def test_create_pump_success(self, auth_client, pump_data):
        response = auth_client.post('/api/v1/pumps/', pump_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['data']['pump_number'] == 'PUMP-001'
        assert response.data['data']['name'] == 'Main Pump 1'
        assert len(response.data['data']['fuel_types']) == 1

    def test_create_pump_duplicate_number(self, auth_client, pump, fuel_type_petrol):
        data = {
            'pump_number': 'PUMP-001',
            'name': 'Another Pump',
            'fuel_type_ids': [str(fuel_type_petrol.uuid)],
        }
        response = auth_client.post('/api/v1/pumps/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_pumps_empty(self, auth_client):
        response = auth_client.get('/api/v1/pumps/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert isinstance(response.data['data'], list)

    def test_list_pumps_with_data(self, auth_client, pump):
        response = auth_client.get('/api/v1/pumps/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) >= 1
        result = response.data['data'][0]
        assert result['pump_number'] == 'PUMP-001'
        assert 'fuel_types' in result
        assert 'active_nozzles' in result

    def test_retrieve_pump(self, auth_client, pump):
        response = auth_client.get(f'/api/v1/pumps/{pump.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['pump_number'] == 'PUMP-001'
        assert response.data['data']['status'] == 'ACTIVE'

    def test_retrieve_pump_not_found(self, auth_client):
        import uuid
        response = auth_client.get(f'/api/v1/pumps/{uuid.uuid4()}/', format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_pump(self, auth_client, pump):
        data = {'name': 'Updated Pump Name', 'location': 'Bay 2'}
        response = auth_client.patch(
            f'/api/v1/pumps/{pump.uuid}/', data, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['name'] == 'Updated Pump Name'
        assert response.data['data']['location'] == 'Bay 2'

    def test_delete_pump(self, auth_client, pump):
        response = auth_client.delete(f'/api/v1/pumps/{pump.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert Pump.objects.filter(uuid=pump.uuid).count() == 0

    def test_create_pump_cashier_forbidden(self, cashier_auth_client, pump_data):
        response = cashier_auth_client.post('/api/v1/pumps/', pump_data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_pump_manager_allowed(self, manager_auth_client, pump_data):
        response = manager_auth_client.post('/api/v1/pumps/', pump_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_unauthenticated_access(self, api_client):
        response = api_client.get('/api/v1/pumps/', format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- Pump Employee Assignment Tests ---


@pytest.mark.django_db
class TestPumpEmployeeAssignment:
    """Tests for assigning employees to pumps."""

    def test_assign_employee_success(self, auth_client, pump, pump_attendant):
        data = {
            'pump': str(pump.uuid),
            'employee': str(pump_attendant.uuid),
        }
        response = auth_client.post('/api/v1/pumps/assign-employee/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['assigned_employee']['uuid'] == str(pump_attendant.uuid)

    def test_assign_cashier_success(self, auth_client, pump, cashier):
        data = {
            'pump': str(pump.uuid),
            'employee': str(cashier.uuid),
        }
        response = auth_client.post('/api/v1/pumps/assign-employee/', data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_assign_invalid_role_rejected(self, auth_client, pump, super_admin):
        data = {
            'pump': str(pump.uuid),
            'employee': str(super_admin.uuid),
        }
        response = auth_client.post('/api/v1/pumps/assign-employee/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_assign_nonexistent_employee(self, auth_client, pump):
        import uuid
        data = {
            'pump': str(pump.uuid),
            'employee': str(uuid.uuid4()),
        }
        response = auth_client.post('/api/v1/pumps/assign-employee/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_assign_nonexistent_pump(self, auth_client, pump_attendant):
        import uuid
        data = {
            'pump': str(uuid.uuid4()),
            'employee': str(pump_attendant.uuid),
        }
        response = auth_client.post('/api/v1/pumps/assign-employee/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_assign_employee_cashier_forbidden(self, cashier_auth_client, pump, pump_attendant):
        data = {
            'pump': str(pump.uuid),
            'employee': str(pump_attendant.uuid),
        }
        response = cashier_auth_client.post('/api/v1/pumps/assign-employee/', data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


# --- Pump Status Update Tests ---


@pytest.mark.django_db
class TestPumpStatusUpdate:
    """Tests for updating pump status."""

    def test_update_status_to_maintenance(self, auth_client, pump):
        data = {
            'pump': str(pump.uuid),
            'status': 'MAINTENANCE',
        }
        response = auth_client.post('/api/v1/pumps/update-status/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['status'] == 'MAINTENANCE'
        assert response.data['data']['last_maintenance_date'] is not None

    def test_update_status_to_inactive(self, auth_client, pump):
        data = {
            'pump': str(pump.uuid),
            'status': 'INACTIVE',
        }
        response = auth_client.post('/api/v1/pumps/update-status/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['status'] == 'INACTIVE'

    def test_update_status_invalid(self, auth_client, pump):
        data = {
            'pump': str(pump.uuid),
            'status': 'INVALID',
        }
        response = auth_client.post('/api/v1/pumps/update-status/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_status_missing_pump(self, auth_client):
        data = {'status': 'MAINTENANCE'}
        response = auth_client.post('/api/v1/pumps/update-status/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_status_cashier_forbidden(self, cashier_auth_client, pump):
        data = {
            'pump': str(pump.uuid),
            'status': 'MAINTENANCE',
        }
        response = cashier_auth_client.post('/api/v1/pumps/update-status/', data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_status_via_patch(self, auth_client, pump):
        data = {
            'pump': str(pump.uuid),
            'status': 'INACTIVE',
        }
        response = auth_client.patch('/api/v1/pumps/update-status/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['status'] == 'INACTIVE'


# --- Nozzle CRUD Tests ---


@pytest.mark.django_db
class TestNozzleCRUD:
    """Tests for nozzle create, read, update, delete."""

    def test_create_nozzle_success(self, auth_client, nozzle_data):
        response = auth_client.post('/api/v1/nozzles/', nozzle_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['data']['nozzle_number'] == 'NOZ-001'
        assert response.data['data']['pump']['pump_number'] == 'PUMP-001'

    def test_create_nozzle_duplicate_number(self, auth_client, nozzle, pump, fuel_type_petrol):
        data = {
            'nozzle_number': 'NOZ-001',
            'pump_id': str(pump.uuid),
            'fuel_type_id': str(fuel_type_petrol.uuid),
        }
        response = auth_client.post('/api/v1/nozzles/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_nozzles_empty(self, auth_client):
        response = auth_client.get('/api/v1/nozzles/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert isinstance(response.data['data'], list)

    def test_list_nozzles_with_data(self, auth_client, nozzle):
        response = auth_client.get('/api/v1/nozzles/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) >= 1

    def test_retrieve_nozzle(self, auth_client, nozzle):
        response = auth_client.get(f'/api/v1/nozzles/{nozzle.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['nozzle_number'] == 'NOZ-001'
        assert 'pump' in response.data['data']
        assert 'fuel_type' in response.data['data']

    def test_retrieve_nozzle_not_found(self, auth_client):
        import uuid
        response = auth_client.get(f'/api/v1/nozzles/{uuid.uuid4()}/', format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_nozzle(self, auth_client, nozzle):
        data = {'status': 'MAINTENANCE'}
        response = auth_client.patch(
            f'/api/v1/nozzles/{nozzle.uuid}/', data, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['status'] == 'MAINTENANCE'

    def test_delete_nozzle(self, auth_client, nozzle):
        response = auth_client.delete(f'/api/v1/nozzles/{nozzle.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert Nozzle.objects.filter(uuid=nozzle.uuid).count() == 0

    def test_create_nozzle_cashier_forbidden(self, cashier_auth_client, nozzle_data):
        response = cashier_auth_client.post('/api/v1/nozzles/', nozzle_data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_nozzle_manager_allowed(self, manager_auth_client, nozzle_data):
        response = manager_auth_client.post('/api/v1/nozzles/', nozzle_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED


# --- Nozzle Meter Update Tests ---


@pytest.mark.django_db
class TestNozzleMeterUpdate:
    """Tests for updating nozzle meter readings."""

    def test_update_meter_success(self, auth_client, nozzle):
        data = {
            'nozzle': str(nozzle.uuid),
            'closing_meter_reading': '150.50',
        }
        response = auth_client.post('/api/v1/nozzles/update-meter/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['closing_meter_reading'] == '150.50'
        assert response.data['data']['current_meter_reading'] == '150.50'

    def test_update_meter_closing_less_than_opening(self, auth_client, nozzle):
        """Closing meter reading must be >= opening meter reading."""
        data = {
            'nozzle': str(nozzle.uuid),
            'closing_meter_reading': '50.00',
        }
        response = auth_client.post('/api/v1/nozzles/update-meter/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_prevent_decreasing_meter(self, auth_client, nozzle):
        """Cannot set closing meter reading less than current meter reading."""
        # First update: set current to 200
        Nozzle.objects.filter(uuid=nozzle.uuid).update(
            current_meter_reading=Decimal('200.00'),
        )
        nozzle.refresh_from_db()

        # Try to set closing to 150 (less than current 200)
        data = {
            'nozzle': str(nozzle.uuid),
            'closing_meter_reading': '150.00',
        }
        response = auth_client.post('/api/v1/nozzles/update-meter/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_meter_nonexistent_nozzle(self, auth_client):
        import uuid
        data = {
            'nozzle': str(uuid.uuid4()),
            'closing_meter_reading': '200.00',
        }
        response = auth_client.post('/api/v1/nozzles/update-meter/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_meter_missing_fields(self, auth_client):
        data = {'nozzle': str(nozzle.uuid) if 'nozzle' in dir() else 'abc'}
        # Send without closing_meter_reading
        import uuid
        data = {'nozzle': str(uuid.uuid4())}
        response = auth_client.post('/api/v1/nozzles/update-meter/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_meter_cashier_forbidden(self, cashier_auth_client, nozzle):
        data = {
            'nozzle': str(nozzle.uuid),
            'closing_meter_reading': '150.00',
        }
        response = cashier_auth_client.post('/api/v1/nozzles/update-meter/', data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
