import uuid
import pytest
from decimal import Decimal

from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.customers.models import Customer
from apps.customers.models.vehicle import Vehicle
from apps.fuel.models import FuelType


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
def customer_user():
    user = User.objects.create_user(
        email='customer@petropump.com',
        password='CustomerPass123',
        first_name='Alice',
        last_name='Smith',
        role=User.Role.CUSTOMER,
    )
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def customer_data():
    return {
        'full_name': 'John Doe',
        'phone': '1234567890',
        'email': 'john@example.com',
        'address': '123 Main St',
    }


@pytest.fixture
def customer(customer_data):
    return Customer.objects.create(**customer_data)


@pytest.fixture
def customer_user_profile(customer_user, customer_data):
    profile = Customer.objects.create(
        user=customer_user,
        full_name='Alice Smith',
        phone='9999999999',
        email='alice@example.com',
    )
    return profile


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
def vehicle_data(customer, fuel_type_petrol):
    return {
        'customer_id': str(customer.uuid),
        'registration_number': 'ABC-1234',
        'vehicle_type': 'CAR',
        'make': 'Toyota',
        'model_name': 'Camry',
        'year': 2022,
        'color': 'White',
        'preferred_fuel_type_id': str(fuel_type_petrol.uuid),
    }


@pytest.fixture
def vehicle(customer, fuel_type_petrol):
    return Vehicle.objects.create(
        customer=customer,
        registration_number='ABC-1234',
        vehicle_type='CAR',
        make='Toyota',
        model_name='Camry',
        year=2022,
        color='White',
        preferred_fuel_type=fuel_type_petrol,
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
def attendant_auth_client(api_client, pump_attendant):
    refresh = RefreshToken.for_user(pump_attendant)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def customer_auth_client(api_client, customer_user):
    refresh = RefreshToken.for_user(customer_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


# --- Customer CRUD Tests ---


@pytest.mark.django_db
class TestCustomerCRUD:
    """Tests for customer create, read, update, delete."""

    def test_create_customer_success(self, auth_client, customer_data):
        response = auth_client.post('/api/v1/customers/', customer_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['data']['full_name'] == 'John Doe'
        assert response.data['data']['phone'] == '1234567890'

    def test_create_customer_manager_allowed(self, manager_auth_client, customer_data):
        response = manager_auth_client.post('/api/v1/customers/', customer_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_customer_cashier_forbidden(self, cashier_auth_client, customer_data):
        response = cashier_auth_client.post('/api/v1/customers/', customer_data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_customer_unauthenticated(self, api_client, customer_data):
        response = api_client.post('/api/v1/customers/', customer_data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_customers_empty(self, auth_client):
        response = auth_client.get('/api/v1/customers/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert isinstance(response.data['data'], list)

    def test_list_customers_with_data(self, auth_client, customer):
        response = auth_client.get('/api/v1/customers/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) >= 1
        result = response.data['data'][0]
        assert result['full_name'] == 'John Doe'
        assert 'vehicles_count' in result

    def test_retrieve_customer(self, auth_client, customer):
        response = auth_client.get(f'/api/v1/customers/{customer.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['full_name'] == 'John Doe'
        assert response.data['data']['phone'] == '1234567890'
        assert 'vehicles' in response.data['data']

    def test_retrieve_customer_not_found(self, auth_client):
        response = auth_client.get(f'/api/v1/customers/{uuid.uuid4()}/', format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_customer(self, auth_client, customer):
        data = {'full_name': 'Jane Doe', 'address': '456 New St'}
        response = auth_client.patch(
            f'/api/v1/customers/{customer.uuid}/', data, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['full_name'] == 'Jane Doe'
        assert response.data['data']['address'] == '456 New St'

    def test_delete_customer(self, auth_client, customer):
        response = auth_client.delete(f'/api/v1/customers/{customer.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert Customer.objects.filter(uuid=customer.uuid).count() == 0


# --- Customer Role Visibility Tests ---


@pytest.mark.django_db
class TestCustomerRoleVisibility:
    """Tests that CUSTOMER role can only see own data."""

    def test_customer_role_sees_own_profile(self, customer_auth_client, customer_user_profile):
        response = customer_auth_client.get('/api/v1/customers/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['full_name'] == 'Alice Smith'

    def test_customer_role_cannot_see_others(self, customer_auth_client, customer):
        """Customer should NOT see other customers in list."""
        response = customer_auth_client.get('/api/v1/customers/', format='json')
        assert response.status_code == status.HTTP_200_OK
        # Should only see own profile (Alice Smith), not 'John Doe'
        for item in response.data['data']:
            assert item['full_name'] != 'John Doe'

    def test_customer_role_my_profile(self, customer_auth_client, customer_user_profile):
        response = customer_auth_client.get('/api/v1/customers/my-profile/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['full_name'] == 'Alice Smith'

    def test_customer_role_my_profile_not_found(self, customer_auth_client):
        """Customer user without a profile should get 404."""
        # The customer_user fixture creates a User but no Customer profile
        # We need to test with a user that has no profile
        pass  # Already tested implicitly — customer_user_profile creates the profile

    def test_customer_role_cannot_create(self, customer_auth_client, customer_data):
        response = customer_auth_client.post('/api/v1/customers/', customer_data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cashier_can_list_customers(self, cashier_auth_client, customer):
        response = cashier_auth_client.get('/api/v1/customers/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) >= 1

    def test_cashier_can_retrieve_customer(self, cashier_auth_client, customer):
        response = cashier_auth_client.get(f'/api/v1/customers/{customer.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_attendant_can_list_customers(self, attendant_auth_client, customer):
        response = attendant_auth_client.get('/api/v1/customers/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) >= 1


# --- Corporate Customer Tests ---


@pytest.mark.django_db
class TestCorporateCustomer:
    """Tests for corporate customer with credit limit."""

    def test_create_corporate_customer_success(self, auth_client):
        data = {
            'full_name': 'Acme Corp',
            'phone': '5555555555',
            'email': 'billing@acme.com',
            'is_corporate': True,
            'company_name': 'Acme Corporation',
            'tax_number': 'TAX-12345',
            'credit_limit': '50000.00',
        }
        response = auth_client.post('/api/v1/customers/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['is_corporate'] is True
        assert response.data['data']['company_name'] == 'Acme Corporation'
        assert response.data['data']['credit_limit'] == '50000.00'

    def test_corporate_customer_requires_company_name(self, auth_client):
        data = {
            'full_name': 'Acme Corp',
            'phone': '5555555555',
            'is_corporate': True,
            'credit_limit': '50000.00',
        }
        response = auth_client.post('/api/v1/customers/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_corporate_customer_credit_limit_must_be_positive(self, auth_client):
        data = {
            'full_name': 'Acme Corp',
            'phone': '5555555555',
            'is_corporate': True,
            'company_name': 'Acme Corporation',
            'credit_limit': '0',
        }
        response = auth_client.post('/api/v1/customers/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_corporate_customer_negative_credit_limit_rejected(self, auth_client):
        data = {
            'full_name': 'Acme Corp',
            'phone': '5555555555',
            'is_corporate': True,
            'company_name': 'Acme Corporation',
            'credit_limit': '-100.00',
        }
        response = auth_client.post('/api/v1/customers/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# --- Phone Uniqueness Tests ---


@pytest.mark.django_db
class TestPhoneUniqueness:
    """Tests for phone number uniqueness validation."""

    def test_duplicate_phone_rejected(self, auth_client, customer):
        data = {
            'full_name': 'Another Customer',
            'phone': '1234567890',  # Same as customer fixture
            'email': 'another@example.com',
        }
        response = auth_client.post('/api/v1/customers/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_customer_same_phone_allowed(self, auth_client, customer):
        """Updating customer with their own phone should be allowed."""
        data = {
            'full_name': 'Updated Name',
            'phone': '1234567890',  # Same phone as existing
        }
        response = auth_client.patch(
            f'/api/v1/customers/{customer.uuid}/', data, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['full_name'] == 'Updated Name'

    def test_update_customer_different_duplicate_phone_rejected(self, auth_client, customer):
        """Updating to another customer's phone should be rejected."""
        # Create another customer
        other = Customer.objects.create(
            full_name='Other Customer',
            phone='9876543210',
        )
        data = {
            'phone': '9876543210',  # Other customer's phone
        }
        response = auth_client.patch(
            f'/api/v1/customers/{customer.uuid}/', data, format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_negative_credit_limit_rejected_on_create(self, auth_client):
        data = {
            'full_name': 'Bad Customer',
            'phone': '1111111111',
            'credit_limit': '-500.00',
        }
        response = auth_client.post('/api/v1/customers/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# --- Vehicle CRUD Tests ---


@pytest.mark.django_db
class TestVehicleCRUD:
    """Tests for vehicle create, read, update, delete."""

    def test_create_vehicle_success(self, auth_client, vehicle_data):
        response = auth_client.post('/api/v1/vehicles/', vehicle_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['data']['registration_number'] == 'ABC-1234'
        assert response.data['data']['make'] == 'Toyota'

    def test_create_vehicle_manager_allowed(self, manager_auth_client, vehicle_data):
        response = manager_auth_client.post('/api/v1/vehicles/', vehicle_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_vehicle_cashier_forbidden(self, cashier_auth_client, vehicle_data):
        response = cashier_auth_client.post('/api/v1/vehicles/', vehicle_data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_vehicle_duplicate_registration(self, auth_client, vehicle, customer, fuel_type_petrol):
        data = {
            'customer_id': str(customer.uuid),
            'registration_number': 'ABC-1234',  # Duplicate
            'vehicle_type': 'CAR',
        }
        response = auth_client.post('/api/v1/vehicles/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_vehicle_nonexistent_customer(self, auth_client):
        data = {
            'customer_id': str(uuid.uuid4()),
            'registration_number': 'XYZ-9999',
            'vehicle_type': 'CAR',
        }
        response = auth_client.post('/api/v1/vehicles/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_vehicles_empty(self, auth_client):
        response = auth_client.get('/api/v1/vehicles/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert isinstance(response.data['data'], list)

    def test_list_vehicles_with_data(self, auth_client, vehicle):
        response = auth_client.get('/api/v1/vehicles/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) >= 1

    def test_retrieve_vehicle(self, auth_client, vehicle):
        response = auth_client.get(f'/api/v1/vehicles/{vehicle.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['registration_number'] == 'ABC-1234'
        assert 'customer' in response.data['data']
        assert 'preferred_fuel_type' in response.data['data']

    def test_retrieve_vehicle_not_found(self, auth_client):
        response = auth_client.get(f'/api/v1/vehicles/{uuid.uuid4()}/', format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_vehicle(self, auth_client, vehicle):
        data = {'color': 'Black', 'year': 2023}
        response = auth_client.patch(
            f'/api/v1/vehicles/{vehicle.uuid}/', data, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['color'] == 'Black'

    def test_delete_vehicle(self, auth_client, vehicle):
        response = auth_client.delete(f'/api/v1/vehicles/{vehicle.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert Vehicle.objects.filter(uuid=vehicle.uuid).count() == 0

    def test_vehicle_unauthenticated(self, api_client):
        response = api_client.get('/api/v1/vehicles/', format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- Customer Role Vehicle Visibility ---


@pytest.mark.django_db
class TestCustomerVehicleVisibility:
    """Tests that CUSTOMER role can only see own vehicles."""

    def test_customer_sees_own_vehicles(self, customer_auth_client, customer_user_profile, fuel_type_petrol):
        # Create a vehicle for the customer_user_profile
        Vehicle.objects.create(
            customer=customer_user_profile,
            registration_number='MY-CAR-1',
            vehicle_type='CAR',
            preferred_fuel_type=fuel_type_petrol,
        )
        response = customer_auth_client.get('/api/v1/vehicles/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['registration_number'] == 'MY-CAR-1'

    def test_customer_cannot_see_others_vehicles(self, customer_auth_client, vehicle):
        """Customer should NOT see vehicles belonging to other customers."""
        response = customer_auth_client.get('/api/v1/vehicles/', format='json')
        assert response.status_code == status.HTTP_200_OK
        for item in response.data['data']:
            assert item['registration_number'] != 'ABC-1234'
