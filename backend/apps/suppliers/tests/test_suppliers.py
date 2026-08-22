import uuid
import pytest

from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.suppliers.models import Supplier


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
        first_name='Inv',
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
        first_name='Jane',
        last_name='Cashier',
        role=User.Role.CASHIER,
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
def supplier():
    return Supplier.objects.create(
        company_name='Global Fuel Corp',
        contact_person='Mike Johnson',
        phone='+1-555-0100',
        email='mike@globalfuel.com',
        address='123 Industrial Ave, Houston, TX',
        tax_number='TAX-GFC-001',
        bank_details='Bank: First National, Acc: 123456789',
        status=Supplier.Status.ACTIVE,
    )


@pytest.fixture
def supplier_data():
    return {
        'company_name': 'Oil Masters Ltd',
        'contact_person': 'Sarah Lee',
        'phone': '+1-555-0200',
        'email': 'sarah@oilmasters.com',
        'address': '456 Oil Street, Dallas, TX',
        'tax_number': 'TAX-OML-002',
        'bank_details': 'Bank: City Bank, Acc: 987654321',
        'status': 'ACTIVE',
    }


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
def inventory_auth_client(api_client, inventory_manager):
    refresh = RefreshToken.for_user(inventory_manager)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def cashier_auth_client(api_client, cashier):
    refresh = RefreshToken.for_user(cashier)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def customer_auth_client(api_client, customer_user):
    refresh = RefreshToken.for_user(customer_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


# --- Supplier CRUD Tests ---


@pytest.mark.django_db
class TestSupplierCRUD:
    """Tests for supplier create, read, update, delete."""

    def test_create_supplier_success(self, auth_client, supplier_data):
        response = auth_client.post('/api/v1/suppliers/', supplier_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['data']['company_name'] == 'Oil Masters Ltd'
        assert response.data['data']['contact_person'] == 'Sarah Lee'

    def test_create_supplier_manager_allowed(self, manager_auth_client, supplier_data):
        response = manager_auth_client.post('/api/v1/suppliers/', supplier_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_supplier_inventory_manager_allowed(self, inventory_auth_client, supplier_data):
        response = inventory_auth_client.post('/api/v1/suppliers/', supplier_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_supplier_cashier_forbidden(self, cashier_auth_client, supplier_data):
        response = cashier_auth_client.post('/api/v1/suppliers/', supplier_data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_supplier_unauthenticated(self, api_client, supplier_data):
        response = api_client.post('/api/v1/suppliers/', supplier_data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_supplier_duplicate_company_name(self, auth_client, supplier):
        data = {
            'company_name': 'Global Fuel Corp',  # duplicate
            'phone': '+1-555-9999',
        }
        response = auth_client.post('/api/v1/suppliers/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_supplier_duplicate_name_inactive_allowed(self, auth_client, supplier):
        """Same company name allowed if existing is INACTIVE."""
        supplier.status = Supplier.Status.INACTIVE
        supplier.save()
        data = {
            'company_name': 'Global Fuel Corp',
            'phone': '+1-555-8888',
        }
        response = auth_client.post('/api/v1/suppliers/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_supplier_invalid_phone(self, auth_client):
        data = {
            'company_name': 'Bad Phone Corp',
            'phone': 'abc-def-ghi',  # invalid
        }
        response = auth_client.post('/api/v1/suppliers/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_suppliers_empty(self, auth_client):
        response = auth_client.get('/api/v1/suppliers/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert isinstance(response.data['data'], list)

    def test_list_suppliers_with_data(self, auth_client, supplier):
        response = auth_client.get('/api/v1/suppliers/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) >= 1
        result = response.data['data'][0]
        assert result['company_name'] == 'Global Fuel Corp'
        assert 'bank_details' not in result  # list serializer excludes it

    def test_retrieve_supplier(self, auth_client, supplier):
        response = auth_client.get(f'/api/v1/suppliers/{supplier.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['company_name'] == 'Global Fuel Corp'
        assert response.data['data']['bank_details'] == 'Bank: First National, Acc: 123456789'

    def test_retrieve_supplier_not_found(self, auth_client):
        response = auth_client.get(f'/api/v1/suppliers/{uuid.uuid4()}/', format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_supplier(self, auth_client, supplier):
        data = {'contact_person': 'New Contact', 'email': 'new@globalfuel.com'}
        response = auth_client.patch(
            f'/api/v1/suppliers/{supplier.uuid}/', data, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['contact_person'] == 'New Contact'
        assert response.data['data']['email'] == 'new@globalfuel.com'

    def test_delete_supplier(self, auth_client, supplier):
        response = auth_client.delete(f'/api/v1/suppliers/{supplier.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert Supplier.objects.filter(uuid=supplier.uuid).count() == 0


# --- Supplier Permission Tests ---


@pytest.mark.django_db
class TestSupplierPermissions:
    """Tests for role-based access to supplier endpoints."""

    def test_cashier_can_list(self, cashier_auth_client, supplier):
        response = cashier_auth_client.get('/api/v1/suppliers/', format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_cashier_can_retrieve(self, cashier_auth_client, supplier):
        response = cashier_auth_client.get(f'/api/v1/suppliers/{supplier.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_cashier_cannot_create(self, cashier_auth_client, supplier_data):
        response = cashier_auth_client.post('/api/v1/suppliers/', supplier_data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cashier_cannot_update(self, cashier_auth_client, supplier):
        response = cashier_auth_client.patch(
            f'/api/v1/suppliers/{supplier.uuid}/',
            {'contact_person': 'Hack'},
            format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cashier_cannot_delete(self, cashier_auth_client, supplier):
        response = cashier_auth_client.delete(f'/api/v1/suppliers/{supplier.uuid}/', format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_inventory_manager_can_update(self, inventory_auth_client, supplier):
        data = {'contact_person': 'Inv Updated'}
        response = inventory_auth_client.patch(
            f'/api/v1/suppliers/{supplier.uuid}/', data, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['contact_person'] == 'Inv Updated'

    def test_inventory_manager_can_delete(self, inventory_auth_client, supplier):
        response = inventory_auth_client.delete(f'/api/v1/suppliers/{supplier.uuid}/', format='json')
        assert response.status_code == status.HTTP_200_OK


# --- Supplier Filtering Tests ---


@pytest.mark.django_db
class TestSupplierFiltering:
    """Tests for supplier filtering."""

    def test_filter_by_status_active(self, auth_client, supplier):
        response = auth_client.get('/api/v1/suppliers/?status=ACTIVE', format='json')
        assert response.status_code == status.HTTP_200_OK
        for item in response.data['data']:
            assert item['status'] == 'ACTIVE'

    def test_filter_by_status_inactive(self, auth_client, supplier):
        supplier.status = Supplier.Status.INACTIVE
        supplier.save()
        response = auth_client.get('/api/v1/suppliers/?status=INACTIVE', format='json')
        assert response.status_code == status.HTTP_200_OK
        for item in response.data['data']:
            assert item['status'] == 'INACTIVE'

    def test_search_by_company_name(self, auth_client, supplier):
        response = auth_client.get('/api/v1/suppliers/?search=Global', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) >= 1
        assert response.data['data'][0]['company_name'] == 'Global Fuel Corp'

    def test_search_by_contact_person(self, auth_client, supplier):
        response = auth_client.get('/api/v1/suppliers/?search=Mike', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) >= 1
        assert response.data['data'][0]['contact_person'] == 'Mike Johnson'

    def test_search_by_phone(self, auth_client, supplier):
        response = auth_client.get('/api/v1/suppliers/?search=0100', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) >= 1

    def test_search_no_results(self, auth_client, supplier):
        response = auth_client.get('/api/v1/suppliers/?search=NonExistent', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 0
