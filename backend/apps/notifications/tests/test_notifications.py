import pytest
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.notifications.models import Notification
from apps.notifications.services import create_notification


@pytest.fixture
def user_one(db):
    return User.objects.create_user(
        email='userone@test.com',
        password='testpass123',
        first_name='User',
        last_name='One',
        role=User.Role.SUPER_ADMIN,
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def user_two(db):
    return User.objects.create_user(
        email='usertwo@test.com',
        password='testpass123',
        first_name='User',
        last_name='Two',
        role=User.Role.CASHIER,
    )


@pytest.fixture
def auth_client_one(user_one):
    client = APIClient()
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user_one)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def auth_client_two(user_two):
    client = APIClient()
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user_two)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def sample_notifications(user_one, user_two):
    notifications = []
    for i in range(5):
        n = Notification.objects.create(
            user=user_one,
            title=f'Notification {i}',
            message=f'Test message {i}',
            notification_type=Notification.NotificationType.GENERAL,
        )
        notifications.append(n)
    # Mark first two as read
    notifications[0].is_read = True
    notifications[0].save(update_fields=['is_read'])
    notifications[1].is_read = True
    notifications[1].save(update_fields=['is_read'])

    # Create notification for user_two
    Notification.objects.create(
        user=user_two,
        title='Other user notification',
        message='Should not be visible to user_one',
        notification_type=Notification.NotificationType.GENERAL,
    )
    return notifications


@pytest.mark.django_db
class TestNotificationList:
    def test_user_can_only_see_own_notifications(self, auth_client_one, sample_notifications, user_one):
        response = auth_client_one.get('/api/v1/notifications/')
        assert response.status_code == status.HTTP_200_OK
        if 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
        # user_one has 5 notifications, user_two has 1
        assert len(results) == 5
        assert all(n['title'].startswith('Notification') for n in results)

    def test_user_cannot_see_other_users_notifications(self, auth_client_two, sample_notifications):
        response = auth_client_two.get('/api/v1/notifications/')
        assert response.status_code == status.HTTP_200_OK
        if 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
        assert len(results) == 1
        assert results[0]['title'] == 'Other user notification'

    def test_unauthenticated_cannot_list(self, api_client, sample_notifications):
        response = api_client.get('/api/v1/notifications/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMarkRead:
    def test_mark_single_notification_read(self, auth_client_one, sample_notifications):
        notification = sample_notifications[2]  # unread
        response = auth_client_one.post(
            f'/api/v1/notifications/{notification.uuid}/mark-read/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        notification.refresh_from_db()
        assert notification.is_read is True

    def test_cannot_mark_other_users_notification(self, auth_client_two, sample_notifications, user_one):
        notification = sample_notifications[2]  # belongs to user_one
        response = auth_client_two.post(
            f'/api/v1/notifications/{notification.uuid}/mark-read/'
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestMarkAllRead:
    def test_mark_all_read(self, auth_client_one, sample_notifications):
        response = auth_client_one.post('/api/v1/notifications/mark-all-read/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        unread = Notification.objects.filter(user__email='userone@test.com', is_read=False).count()
        assert unread == 0


@pytest.mark.django_db
class TestUnreadCount:
    def test_unread_count(self, auth_client_one, sample_notifications):
        response = auth_client_one.get('/api/v1/notifications/unread-count/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['count'] == 3  # 5 total - 2 read

    def test_unread_count_after_mark_all(self, auth_client_one, sample_notifications):
        auth_client_one.post('/api/v1/notifications/mark-all-read/')
        response = auth_client_one.get('/api/v1/notifications/unread-count/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['count'] == 0


@pytest.mark.django_db
class TestNotificationPermissions:
    def test_cannot_retrieve_other_users_notification(self, auth_client_two, sample_notifications):
        notification = sample_notifications[0]  # belongs to user_one
        response = auth_client_two.get(f'/api/v1/notifications/{notification.uuid}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_can_retrieve_own_notification(self, auth_client_one, sample_notifications):
        notification = sample_notifications[0]
        response = auth_client_one.get(f'/api/v1/notifications/{notification.uuid}/')
        assert response.status_code == status.HTTP_200_OK
