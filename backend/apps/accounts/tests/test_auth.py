import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User


# --- Fixtures ---


@pytest.fixture
def super_admin_data():
    return {
        'email': 'admin@petropump.com',
        'password': 'AdminPass123',
        'first_name': 'System',
        'last_name': 'Administrator',
        'role': User.Role.SUPER_ADMIN,
    }


@pytest.fixture
def super_admin(super_admin_data):
    return User.objects.create_superuser(
        email=super_admin_data['email'],
        password=super_admin_data['password'],
        first_name=super_admin_data['first_name'],
        last_name=super_admin_data['last_name'],
    )


@pytest.fixture
def active_user_data():
    return {
        'email': 'cashier@petropump.com',
        'password': 'CashierPass123',
        'first_name': 'John',
        'last_name': 'Doe',
        'role': User.Role.CASHIER,
    }


@pytest.fixture
def active_user(active_user_data):
    user = User.objects.create_user(
        email=active_user_data['email'],
        password=active_user_data['password'],
        first_name=active_user_data['first_name'],
        last_name=active_user_data['last_name'],
        role=active_user_data['role'],
    )
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def unverified_user_data():
    return {
        'email': 'unverified@petropump.com',
        'password': 'UnverifiedPass123',
        'first_name': 'Jane',
        'last_name': 'Smith',
        'role': User.Role.CASHIER,
    }


@pytest.fixture
def unverified_user(unverified_user_data):
    user = User.objects.create_user(
        email=unverified_user_data['email'],
        password=unverified_user_data['password'],
        first_name=unverified_user_data['first_name'],
        last_name=unverified_user_data['last_name'],
        role=unverified_user_data['role'],
    )
    user.is_verified = False
    user.save()
    return user


@pytest.fixture
def inactive_user_data():
    return {
        'email': 'inactive@petropump.com',
        'password': 'InactivePass123',
        'first_name': 'Bob',
        'last_name': 'Wilson',
        'role': User.Role.CASHIER,
    }


@pytest.fixture
def inactive_user(inactive_user_data):
    user = User.objects.create_user(
        email=inactive_user_data['email'],
        password=inactive_user_data['password'],
        first_name=inactive_user_data['first_name'],
        last_name=inactive_user_data['last_name'],
        role=inactive_user_data['role'],
    )
    user.is_active = False
    user.save()
    return user


@pytest.fixture
def auth_tokens(active_user):
    refresh = RefreshToken.for_user(active_user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


@pytest.fixture
def admin_auth_tokens(super_admin):
    refresh = RefreshToken.for_user(super_admin)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


@pytest.fixture
def auth_client(api_client, auth_tokens):
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_tokens["access"]}')
    return api_client


@pytest.fixture
def admin_auth_client(api_client, admin_auth_tokens):
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_auth_tokens["access"]}')
    return api_client


# --- Login Tests ---


@pytest.mark.django_db
class TestLoginView:
    """Tests for POST /api/v1/auth/login/"""

    def test_login_success(self, api_client, active_user, active_user_data):
        """Successful login returns tokens and user info."""
        url = reverse('login')
        data = {
            'email': active_user_data['email'],
            'password': active_user_data['password'],
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['message'] == 'Login successful.'
        assert 'access' in response.data['data']
        assert 'refresh' in response.data['data']
        assert 'user' in response.data['data']
        assert response.data['data']['user']['email'] == active_user_data['email']
        assert response.data['data']['user']['role'] == User.Role.CASHIER
        assert response.data['data']['user']['role_display'] == 'Cashier'

    def test_login_invalid_credentials(self, api_client, active_user):
        """Login with wrong password returns 401."""
        url = reverse('login')
        data = {
            'email': active_user.email,
            'password': 'WrongPassword999',
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False
        assert 'Invalid email or password' in response.data['message']

    def test_login_nonexistent_email(self, api_client):
        """Login with non-existent email returns 401."""
        url = reverse('login')
        data = {
            'email': 'nonexistent@example.com',
            'password': 'SomePassword123',
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False

    def test_login_missing_email(self, api_client):
        """Login without email returns validation error."""
        url = reverse('login')
        data = {'password': 'SomePassword123'}
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    def test_login_missing_password(self, api_client, active_user):
        """Login without password returns validation error."""
        url = reverse('login')
        data = {'email': active_user.email}
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    def test_login_missing_both_fields(self, api_client):
        """Login without email and password returns validation error."""
        url = reverse('login')
        data = {}
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    def test_login_inactive_user(self, api_client, inactive_user, inactive_user_data):
        """Login with inactive user returns error.
        Django's ModelBackend returns None for inactive users for security,
        so the error message is the same as invalid credentials.
        """
        url = reverse('login')
        data = {
            'email': inactive_user_data['email'],
            'password': inactive_user_data['password'],
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False
        assert 'Invalid email or password' in response.data['message']

    def test_login_unverified_user(self, api_client, unverified_user, unverified_user_data):
        """Login with unverified non-admin user returns error."""
        url = reverse('login')
        data = {
            'email': unverified_user_data['email'],
            'password': unverified_user_data['password'],
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False
        assert 'not been verified' in response.data['message']

    def test_login_unverified_super_admin_succeeds(self, api_client, super_admin, super_admin_data):
        """Unverified SUPER_ADMIN can still login."""
        super_admin.is_verified = False
        super_admin.save()

        url = reverse('login')
        data = {
            'email': super_admin_data['email'],
            'password': super_admin_data['password'],
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True


# --- Token Refresh Tests ---


@pytest.mark.django_db
class TestTokenRefresh:
    """Tests for JWT token refresh."""

    def test_refresh_token_success(self, api_client, active_user):
        """Refreshing a valid token returns new tokens."""
        refresh = RefreshToken.for_user(active_user)
        url = reverse('token_refresh')
        data = {'refresh': str(refresh)}
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_refresh_token_invalid(self, api_client):
        """Refreshing with an invalid token returns error."""
        url = reverse('token_refresh')
        data = {'refresh': 'invalidtoken123'}
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- Profile Tests ---


@pytest.mark.django_db
class TestProfileView:
    """Tests for GET /api/v1/auth/profile/"""

    def test_profile_authenticated(self, auth_client, active_user):
        """Authenticated user can access their profile."""
        url = reverse('profile')
        response = auth_client.get(url, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['email'] == active_user.email
        assert response.data['data']['first_name'] == active_user.first_name
        assert response.data['data']['last_name'] == active_user.last_name
        assert response.data['data']['role'] == active_user.role
        assert 'full_name' in response.data['data']
        assert response.data['data']['full_name'] == 'John Doe'

    def test_profile_unauthenticated(self, api_client):
        """Unauthenticated user cannot access profile."""
        url = reverse('profile')
        response = api_client.get(url, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_profile_returns_expected_fields(self, auth_client, active_user):
        """Profile response includes all expected fields."""
        url = reverse('profile')
        response = auth_client.get(url, format='json')
        data = response.data['data']

        expected_fields = [
            'uuid', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'role', 'role_display', 'is_active', 'is_verified',
            'created_at', 'updated_at',
        ]
        for field in expected_fields:
            assert field in data, f'Missing field: {field}'


# --- Logout Tests ---


@pytest.mark.django_db
class TestLogoutView:
    """Tests for POST /api/v1/auth/logout/"""

    def test_logout_success(self, auth_client, active_user):
        """Authenticated user can logout by blacklisting refresh token."""
        refresh = RefreshToken.for_user(active_user)
        url = reverse('logout')
        data = {'refresh': str(refresh)}
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['message'] == 'Logout successful.'

    def test_logout_missing_refresh_token(self, auth_client):
        """Logout without refresh token returns 400."""
        url = reverse('logout')
        data = {}
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'Refresh token is required' in response.data['message']

    def test_logout_unauthenticated(self, api_client):
        """Unauthenticated user cannot logout."""
        url = reverse('logout')
        data = {'refresh': 'sometoken'}
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_invalid_token(self, auth_client):
        """Logout with invalid token returns 400."""
        url = reverse('logout')
        data = {'refresh': 'invalidtoken123'}
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
