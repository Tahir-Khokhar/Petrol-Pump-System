import pytest
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.audit_logs.models import AuditLog
from apps.audit_logs.utils import create_audit_log


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email='admin@test.com',
        password='testpass123',
        first_name='Admin',
        last_name='User',
        role=User.Role.SUPER_ADMIN,
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def manager_user(db):
    return User.objects.create_user(
        email='manager@test.com',
        password='testpass123',
        first_name='Manager',
        last_name='User',
        role=User.Role.PUMP_MANAGER,
        is_staff=True,
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
def audit_logs(admin_user):
    logs = []
    for action in ['LOGIN', 'CREATE', 'UPDATE', 'DELETE']:
        logs.append(
            AuditLog.objects.create(
                user=admin_user,
                action=action,
                model_name='accounts.User',
                object_id=str(admin_user.uuid),
                description=f'Test {action} action',
            )
        )
    return logs


@pytest.fixture
def authenticated_admin_client(admin_user):
    client = APIClient()
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(admin_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def authenticated_manager_client(manager_user):
    client = APIClient()
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(manager_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def authenticated_cashier_client(cashier_user):
    client = APIClient()
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(cashier_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.mark.django_db
class TestAuditLogListing:
    def test_admin_can_list_audit_logs(self, authenticated_admin_client, audit_logs):
        response = authenticated_admin_client.get('/api/v1/audit-logs/')
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        # Paginated response
        if 'results' in data:
            results = data['results']
        else:
            results = data
        assert len(results) == 4

    def test_manager_can_list_audit_logs(self, authenticated_manager_client, audit_logs):
        response = authenticated_manager_client.get('/api/v1/audit-logs/')
        assert response.status_code == status.HTTP_200_OK

    def test_cashier_cannot_list_audit_logs(self, authenticated_cashier_client, audit_logs):
        response = authenticated_cashier_client.get('/api/v1/audit-logs/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_list_audit_logs(self, api_client, audit_logs):
        response = api_client.get('/api/v1/audit-logs/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAuditLogFiltering:
    def test_filter_by_action(self, authenticated_admin_client, audit_logs):
        response = authenticated_admin_client.get('/api/v1/audit-logs/', {'action': 'LOGIN'})
        assert response.status_code == status.HTTP_200_OK
        if 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
        assert len(results) == 1
        assert results[0]['action'] == 'LOGIN'

    def test_filter_by_date_range(self, authenticated_admin_client, audit_logs):
        from datetime import datetime, timedelta, timezone
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        response = authenticated_admin_client.get(
            '/api/v1/audit-logs/',
            {'date_from': yesterday, 'date_to': tomorrow},
        )
        assert response.status_code == status.HTTP_200_OK
        if 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
        assert len(results) == 4

    def test_filter_by_model_name(self, authenticated_admin_client, audit_logs):
        response = authenticated_admin_client.get(
            '/api/v1/audit-logs/', {'model_name': 'accounts.User'}
        )
        assert response.status_code == status.HTTP_200_OK
        if 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
        assert len(results) == 4
        assert all(r['model_name'] == 'accounts.User' for r in results)


@pytest.mark.django_db
class TestCreateAuditLogUtility:
    def test_create_audit_log_success(self, admin_user):
        create_audit_log(
            user=admin_user,
            action='CREATE',
            model_name='test.Model',
            object_id='123',
            description='Test audit log',
        )
        assert AuditLog.objects.count() == 1
        log = AuditLog.objects.first()
        assert log.action == 'CREATE'
        assert log.model_name == 'test.Model'
        assert log.object_id == '123'
        assert log.description == 'Test audit log'

    def test_create_audit_log_with_none_user(self, db):
        create_audit_log(
            user=None,
            action='OTHER',
            description='System action',
        )
        assert AuditLog.objects.count() == 1
        log = AuditLog.objects.first()
        assert log.user is None
