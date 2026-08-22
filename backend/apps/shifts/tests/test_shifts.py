import pytest
from decimal import Decimal
from datetime import date

from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.fuel.models import FuelType
from apps.pumps.models import Pump, Nozzle
from apps.shifts.models import Shift, MeterReading


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
def cashier_user(db):
    return User.objects.create_user(
        email='cashier@test.com',
        password='testpass123',
        first_name='Cashier',
        last_name='User',
        role=User.Role.CASHIER,
    )


@pytest.fixture
def pump_attendant_user(db):
    return User.objects.create_user(
        email='attendant@test.com',
        password='testpass123',
        first_name='Attendant',
        last_name='User',
        role=User.Role.PUMP_ATTENDANT,
    )


@pytest.fixture
def auth_client(super_admin_user):
    client = APIClient()
    client.force_authenticate(user=super_admin_user)
    return client


@pytest.fixture
def cashier_client(cashier_user):
    client = APIClient()
    client.force_authenticate(user=cashier_user)
    return client


@pytest.fixture
def attendant_client(pump_attendant_user):
    client = APIClient()
    client.force_authenticate(user=pump_attendant_user)
    return client


@pytest.fixture
def fuel_type(db):
    return FuelType.objects.create(
        name='Petrol',
        code='PET',
        current_price=Decimal('90.00'),
    )


@pytest.fixture
def pump(db):
    return Pump.objects.create(
        pump_number='PUMP-001',
        name='Main Pump',
    )


@pytest.fixture
def nozzle(db, pump, fuel_type):
    return Nozzle.objects.create(
        nozzle_number='NOZ-001',
        pump=pump,
        fuel_type=fuel_type,
    )


@pytest.mark.django_db
class TestOpenCloseShift:
    """Tests for opening and closing shifts."""

    def test_open_shift(self, cashier_client, cashier_user, pump):
        data = {
            'employee': str(cashier_user.uuid),
            'pump': str(pump.uuid),
            'opening_cash': '5000.00',
        }
        response = cashier_client.post('/api/v1/shifts/open/', data, format='json')
        assert response.status_code == 201
        assert response.data['success'] is True
        assert response.data['data']['status'] == 'OPEN'
        assert Shift.objects.filter(status=Shift.Status.OPEN).exists()

    def test_close_shift(self, cashier_client, cashier_user, pump):
        # Open shift first
        data = {
            'employee': str(cashier_user.uuid),
            'pump': str(pump.uuid),
            'opening_cash': '5000.00',
        }
        open_resp = cashier_client.post('/api/v1/shifts/open/', data, format='json')
        shift_uuid = open_resp.data['data']['uuid']

        # Close shift
        close_data = {'actual_cash': '7500.00'}
        response = cashier_client.post(
            f'/api/v1/shifts/close/{shift_uuid}/', close_data, format='json'
        )
        assert response.status_code == 200
        assert response.data['success'] is True
        assert response.data['data']['status'] == 'CLOSED'

    def test_duplicate_open_prevented(self, cashier_client, cashier_user, pump):
        data = {
            'employee': str(cashier_user.uuid),
            'pump': str(pump.uuid),
            'opening_cash': '5000.00',
        }
        cashier_client.post('/api/v1/shifts/open/', data, format='json')

        # Try to open another shift on the same pump
        response = cashier_client.post('/api/v1/shifts/open/', data, format='json')
        assert response.status_code == 400

    def test_cannot_close_already_closed_shift(self, cashier_client, cashier_user, pump):
        data = {
            'employee': str(cashier_user.uuid),
            'pump': str(pump.uuid),
            'opening_cash': '5000.00',
        }
        open_resp = cashier_client.post('/api/v1/shifts/open/', data, format='json')
        shift_uuid = open_resp.data['data']['uuid']

        # Close once
        cashier_client.post(
            f'/api/v1/shifts/close/{shift_uuid}/', {'actual_cash': '5000.00'}, format='json'
        )

        # Try to close again
        response = cashier_client.post(
            f'/api/v1/shifts/close/{shift_uuid}/', {'actual_cash': '5000.00'}, format='json'
        )
        assert response.status_code == 400

    def test_list_shifts(self, auth_client, cashier_user, pump):
        data = {
            'employee': str(cashier_user.uuid),
            'pump': str(pump.uuid),
            'opening_cash': '5000.00',
        }
        cashier_client = APIClient()
        cashier_client.force_authenticate(user=cashier_user)
        cashier_client.post('/api/v1/shifts/open/', data, format='json')

        response = auth_client.get('/api/v1/shifts/shifts/', format='json')
        assert response.status_code == 200
        assert response.data['success'] is True

    def test_cashier_sees_own_shifts(self, cashier_client, cashier_user, pump):
        data = {
            'employee': str(cashier_user.uuid),
            'pump': str(pump.uuid),
            'opening_cash': '5000.00',
        }
        cashier_client.post('/api/v1/shifts/open/', data, format='json')

        response = cashier_client.get('/api/v1/shifts/shifts/', format='json')
        assert response.status_code == 200
        for shift_data in response.data['data']:
            assert str(shift_data['employee']) == str(cashier_user.uuid)


@pytest.mark.django_db
class TestMeterReading:
    """Tests for meter reading CRUD."""

    def test_create_meter_reading(self, auth_client, super_admin_user, pump, nozzle):
        # Create a shift first
        from apps.shifts.services import open_shift
        shift = open_shift(super_admin_user, pump, Decimal('5000.00'), super_admin_user)

        data = {
            'shift': str(shift.uuid),
            'nozzle': str(nozzle.uuid),
            'opening_reading': '100.00',
            'date': str(date.today()),
        }
        response = auth_client.post('/api/v1/meter-readings/meter-readings/', data, format='json')
        assert response.status_code == 201
        assert response.data['success'] is True

    def test_meter_reading_with_closing(self, auth_client, super_admin_user, pump, nozzle):
        from apps.shifts.services import open_shift
        shift = open_shift(super_admin_user, pump, Decimal('5000.00'), super_admin_user)

        data = {
            'shift': str(shift.uuid),
            'nozzle': str(nozzle.uuid),
            'opening_reading': '100.00',
            'closing_reading': '150.00',
            'date': str(date.today()),
        }
        response = auth_client.post('/api/v1/meter-readings/meter-readings/', data, format='json')
        assert response.status_code == 201
        assert response.data['data']['fuel_dispensed'] == '50.00'

    def test_closing_less_than_opening_fails(self, auth_client, super_admin_user, pump, nozzle):
        from apps.shifts.services import open_shift
        shift = open_shift(super_admin_user, pump, Decimal('5000.00'), super_admin_user)

        data = {
            'shift': str(shift.uuid),
            'nozzle': str(nozzle.uuid),
            'opening_reading': '150.00',
            'closing_reading': '100.00',
            'date': str(date.today()),
        }
        response = auth_client.post('/api/v1/meter-readings/meter-readings/', data, format='json')
        assert response.status_code == 400

    def test_pump_attendant_can_create_meter_reading(self, attendant_client, super_admin_user, pump, nozzle):
        from apps.shifts.services import open_shift
        shift = open_shift(super_admin_user, pump, Decimal('5000.00'), super_admin_user)

        data = {
            'shift': str(shift.uuid),
            'nozzle': str(nozzle.uuid),
            'opening_reading': '100.00',
            'date': str(date.today()),
        }
        response = attendant_client.post('/api/v1/meter-readings/meter-readings/', data, format='json')
        assert response.status_code == 201
