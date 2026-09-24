from rest_framework import generics, status, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    ChangePasswordSerializer,
    UserUpdateSerializer,
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
)
from .permissions import IsOwnerOrAdmin, IsAdminUser, TenantIsolationPermission

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration.

    POST /api/v1/accounts/register/
    - Creates a new user account
    - Returns user data and JWT tokens
    - No authentication required
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'message': 'Registration successful.'
            }, status=status.HTTP_201_CREATED)

        except ValidationError as exc:
            return Response({
                'error': 'Registration failed.',
                'detail': exc.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({
                'error': 'Registration failed.',
                'detail': 'Invalid registration data.'
            }, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    API endpoint for user login.

    POST /api/v1/accounts/login/
    - Authenticates user with email and password
    - Returns JWT tokens and user data
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)

            if response.status_code == 200:
                # Update last login
                user = User.objects.get(email=request.data.get('email'))
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])

                response.data['message'] = 'Login successful.'

            return response

        except Exception:
            return Response({
                'error': 'Login failed.',
                'detail': 'Invalid credentials.'
            }, status=status.HTTP_401_UNAUTHORIZED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for viewing and updating user profile.

    GET /api/v1/accounts/me/
    - Returns current user profile

    PUT/PATCH /api/v1/accounts/me/
    - Updates current user profile
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', True)
            instance = self.get_object()
            serializer = UserUpdateSerializer(
                instance,
                data=request.data,
                partial=partial,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response({
                **UserSerializer(instance).data,
                'message': 'Profile updated successfully.'
            }, status=status.HTTP_200_OK)

        except ValidationError as exc:
            return Response({
                'error': 'Profile update failed.',
                'detail': exc.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({
                'error': 'Profile update failed.',
                'detail': 'Invalid profile data.'
            }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    API endpoint for changing user password.

    POST /api/v1/accounts/change-password/
    - Changes password for authenticated user
    - Requires old password verification
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            serializer = ChangePasswordSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)

            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            return Response({
                'message': 'Password updated successfully.'
            }, status=status.HTTP_200_OK)

        except ValidationError as exc:
            return Response({
                'error': 'Password change failed.',
                'detail': exc.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({
                'error': 'Password change failed.',
                'detail': 'Invalid data provided.'
            }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    API endpoint for user logout.

    POST /api/v1/accounts/logout/
    - Blacklists refresh token
    - Requires authentication
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            serializer = LogoutSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            refresh_token = serializer.validated_data['refresh_token']
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({
                'message': 'Successfully logged out.'
            }, status=status.HTTP_200_OK)

        except TokenError:
            return Response({
                'error': 'Logout failed.',
                'detail': 'Invalid token or token already blacklisted.'
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response({
                'error': 'Logout failed.',
                'detail': 'Invalid logout request.'
            }, status=status.HTTP_400_BAD_REQUEST)


class HealthCheckView(APIView):
    """
    API endpoint for health check.

    GET /api/health/
    - Returns API health status
    - No authentication required
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            # Check database connection
            User.objects.exists()

            return Response({
                'status': 'ok',
                'timestamp': timezone.now().isoformat(),
                'service': 'UniPath MAX API',
                'version': '1.0.0',
                'build_commit': getattr(settings, 'BUILD_COMMIT_SHA', '') or None,
                'build_fingerprint': getattr(settings, 'BUILD_FINGERPRINT', '') or None,
            }, status=status.HTTP_200_OK)

        except Exception:
            return Response({
                'status': 'unhealthy',
                'timestamp': timezone.now().isoformat(),
                'error': 'Health check failed.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class UserViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for user management (Admin only).

    Provides CRUD operations for user management with tenant isolation.
    Only accessible to admin users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    filterset_fields = ['role', 'university', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'university']
    ordering_fields = ['date_joined', 'email', 'role']
    ordering = ['-date_joined']

    def get_queryset(self):
        """
        Filter queryset based on user role for tenant isolation.
        Platform superusers see all users; tenant admins see only their university.
        """
        user = self.request.user
        queryset = User.objects.all()

        # Tenant isolation: role='admin' is a university admin in the demo.
        if not user.is_superuser:
            queryset = queryset.filter(university=user.university)

        # Apply search filter
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(university__icontains=search_query)
            )

        return queryset

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get user statistics.

        GET /api/v1/accounts/users/stats/
        """
        queryset = self.get_queryset()

        stats = {
            'total_users': queryset.count(),
            'active_users': queryset.filter(is_active=True).count(),
            'by_role': {
                'students': queryset.filter(role='student').count(),
                'mentors': queryset.filter(role='mentor').count(),
                'organizers': queryset.filter(role='organizer').count(),
                'admins': queryset.filter(role='admin').count(),
            }
        }

        return Response(stats, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a user account.

        POST /api/v1/accounts/users/{id}/deactivate/
        """
        user = self.get_object()

        if user == request.user:
            return Response({
                'error': 'Cannot deactivate your own account.'
            }, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = False
        user.save()

        return Response({
            'message': f'User {user.email} has been deactivated.'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a user account.

        POST /api/v1/accounts/users/{id}/activate/
        """
        user = self.get_object()
        user.is_active = True
        user.save()

        return Response({
            'message': f'User {user.email} has been activated.'
        }, status=status.HTTP_200_OK)
