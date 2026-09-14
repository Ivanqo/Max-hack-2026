import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


@pytest.fixture
def api_client():
    """Create an API client for testing."""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
        role='student',
        university='Test University'
    )


@pytest.mark.django_db
class TestUserRegistration:
    """Tests for user registration endpoint."""

    def test_user_registration_success(self, api_client):
        """Test successful user registration."""
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123!',
            'password2': 'newpass123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'student',
            'university': 'Test University'
        }
        response = api_client.post('/api/auth/register/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'tokens' in response.data
        assert response.data['user']['email'] == 'newuser@example.com'

    def test_user_registration_password_mismatch(self, api_client):
        """Test registration fails when passwords don't match."""
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123!',
            'password2': 'differentpass123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'student'
        }
        response = api_client.post('/api/auth/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserLogin:
    """Tests for user login endpoint."""

    def test_user_login_success(self, api_client, test_user):
        """Test successful user login."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = api_client.post('/api/auth/login/', data)

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_user_login_invalid_credentials(self, api_client, test_user):
        """Test login fails with invalid credentials."""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = api_client.post('/api/auth/login/', data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserProfile:
    """Tests for user profile endpoint."""

    def test_get_profile_authenticated(self, api_client, test_user):
        """Test authenticated user can retrieve their profile."""
        api_client.force_authenticate(user=test_user)
        response = api_client.get('/api/auth/profile/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'test@example.com'
        assert response.data['role'] == 'student'

    def test_get_profile_unauthenticated(self, api_client):
        """Test unauthenticated user cannot retrieve profile."""
        response = api_client.get('/api/auth/profile/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile(self, api_client, test_user):
        """Test authenticated user can update their profile."""
        api_client.force_authenticate(user=test_user)
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'university': 'New University'
        }
        response = api_client.patch('/api/auth/profile/', data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Updated'
        assert response.data['university'] == 'New University'


@pytest.mark.django_db
class TestChangePassword:
    """Tests for password change endpoint."""

    def test_change_password_success(self, api_client, test_user):
        """Test successful password change."""
        api_client.force_authenticate(user=test_user)
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass456!',
            'new_password2': 'newpass456!'
        }
        response = api_client.post('/api/auth/change-password/', data)

        assert response.status_code == status.HTTP_200_OK

        test_user.refresh_from_db()
        assert test_user.check_password('newpass456!')

    def test_change_password_wrong_old_password(self, api_client, test_user):
        """Test password change fails with wrong old password."""
        api_client.force_authenticate(user=test_user)
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass456!',
            'new_password2': 'newpass456!'
        }
        response = api_client.post('/api/auth/change-password/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
