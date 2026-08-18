import pytest
from decimal import Decimal
from datetime import date, timedelta

from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.expenses.models import Expense


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
def accountant_user(db):
    return User.objects.create_user(
        email='accountant@test.com',
        password='testpass123',
        first_name='Accountant',
        last_name='User',
        role=User.Role.ACCOUNTANT,
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
def accountant_client(accountant_user):
    client = APIClient()
    client.force_authenticate(user=accountant_user)
    return client


@pytest.fixture
def cashier_client(cashier_user):
    client = APIClient()
    client.force_authenticate(user=cashier_user)
    return client


@pytest.mark.django_db
class TestExpenseCRUD:
    """Tests for expense CRUD operations."""

    def test_create_expense(self, auth_client):
        data = {
            'category': 'ELECTRICITY',
            'amount': '5000.00',
            'description': 'Monthly electricity bill',
            'expense_date': str(date.today()),
            'payment_method': 'BANK_TRANSFER',
        }
        response = auth_client.post('/api/v1/expenses/expenses/', data, format='json')
        assert response.status_code == 201
        assert response.data['success'] is True
        assert response.data['data']['category'] == 'ELECTRICITY'
        assert response.data['data']['amount'] == '5000.00'

    def test_list_expenses(self, auth_client):
        data = {
            'category': 'RENT',
            'amount': '10000.00',
            'description': 'Monthly rent',
            'expense_date': str(date.today()),
        }
        auth_client.post('/api/v1/expenses/expenses/', data, format='json')

        response = auth_client.get('/api/v1/expenses/expenses/', format='json')
        assert response.status_code == 200
        assert response.data['success'] is True
        assert len(response.data['data']) >= 1

    def test_retrieve_expense(self, auth_client):
        data = {
            'category': 'MAINTENANCE',
            'amount': '2500.00',
            'description': 'Pump maintenance',
            'expense_date': str(date.today()),
        }
        create_resp = auth_client.post('/api/v1/expenses/expenses/', data, format='json')
        expense_uuid = create_resp.data['data']['uuid']

        response = auth_client.get(f'/api/v1/expenses/expenses/{expense_uuid}/', format='json')
        assert response.status_code == 200
        assert response.data['data']['uuid'] == expense_uuid

    def test_update_expense(self, auth_client):
        data = {
            'category': 'CLEANING',
            'amount': '1500.00',
            'description': 'Cleaning service',
            'expense_date': str(date.today()),
        }
        create_resp = auth_client.post('/api/v1/expenses/expenses/', data, format='json')
        expense_uuid = create_resp.data['data']['uuid']

        update_data = {'description': 'Updated cleaning description'}
        response = auth_client.patch(
            f'/api/v1/expenses/expenses/{expense_uuid}/', update_data, format='json'
        )
        assert response.status_code == 200
        assert response.data['data']['description'] == 'Updated cleaning description'

    def test_delete_expense(self, auth_client):
        data = {
            'category': 'OTHER',
            'amount': '300.00',
            'description': 'Misc expense',
            'expense_date': str(date.today()),
        }
        create_resp = auth_client.post('/api/v1/expenses/expenses/', data, format='json')
        expense_uuid = create_resp.data['data']['uuid']

        response = auth_client.delete(f'/api/v1/expenses/expenses/{expense_uuid}/', format='json')
        assert response.status_code == 200
        assert not Expense.objects.filter(uuid=expense_uuid).exists()

    def test_cashier_cannot_create_expense(self, cashier_client):
        data = {
            'category': 'OTHER',
            'amount': '100.00',
            'description': 'Test',
            'expense_date': str(date.today()),
        }
        response = cashier_client.post('/api/v1/expenses/expenses/', data, format='json')
        assert response.status_code == 403

    def test_accountant_can_create_expense(self, accountant_client):
        data = {
            'category': 'SALARIES',
            'amount': '50000.00',
            'description': 'Monthly salaries',
            'expense_date': str(date.today()),
        }
        response = accountant_client.post('/api/v1/expenses/expenses/', data, format='json')
        assert response.status_code == 201

    def test_amount_must_be_positive(self, auth_client):
        data = {
            'category': 'OTHER',
            'amount': '0',
            'description': 'Test',
            'expense_date': str(date.today()),
        }
        response = auth_client.post('/api/v1/expenses/expenses/', data, format='json')
        assert response.status_code == 400

    def test_future_date_rejected(self, auth_client):
        future_date = date.today() + timedelta(days=10)
        data = {
            'category': 'OTHER',
            'amount': '100.00',
            'description': 'Test',
            'expense_date': str(future_date),
        }
        response = auth_client.post('/api/v1/expenses/expenses/', data, format='json')
        assert response.status_code == 400

    def test_category_filter(self, auth_client):
        auth_client.post('/api/v1/expenses/expenses/', {
            'category': 'ELECTRICITY',
            'amount': '5000.00',
            'description': 'Electricity',
            'expense_date': str(date.today()),
        }, format='json')
        auth_client.post('/api/v1/expenses/expenses/', {
            'category': 'RENT',
            'amount': '10000.00',
            'description': 'Rent',
            'expense_date': str(date.today()),
        }, format='json')

        response = auth_client.get('/api/v1/expenses/expenses/?category=ELECTRICITY', format='json')
        assert response.status_code == 200
        for expense in response.data['data']:
            assert expense['category'] == 'ELECTRICITY'
