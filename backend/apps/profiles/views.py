from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from .models import StudentProfile, CareerGoal
from .serializers import (
    StudentProfileSerializer,
    StudentProfileCreateSerializer,
    StudentProfileUpdateSerializer,
    CareerGoalSerializer,
    OnboardingCompleteSerializer,
    SkillsUpdateSerializer
)
from .permissions import (
    IsOwnerOrAdmin,
    IsStudentOrAdmin,
    TenantIsolationPermission,
    CanCompleteOnboarding,
    IsAdminOrReadOnly
)


class StudentProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing student profiles with tenant isolation.

    Endpoints:
    - GET /profiles/ - List all profiles (filtered by tenant)
    - POST /profiles/ - Create a new profile
    - GET /profiles/{id}/ - Retrieve a specific profile
    - PUT /profiles/{id}/ - Update a profile
    - PATCH /profiles/{id}/ - Partial update a profile
    - DELETE /profiles/{id}/ - Delete a profile
    - POST /profiles/{id}/complete-onboarding/ - Complete onboarding
    - POST /profiles/{id}/update-skills/ - Update skills/interests
    - GET /profiles/me/ - Get current user's profile
    """

    queryset = StudentProfile.objects.select_related('user', 'career_goal').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['university', 'institute', 'course', 'onboarding_completed']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'university', 'program']
    ordering_fields = ['created_at', 'updated_at', 'course']
    ordering = ['-created_at']

    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action == 'create':
            permission_classes = [IsAuthenticated, IsStudentOrAdmin]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsOwnerOrAdmin, TenantIsolationPermission]
        elif self.action == 'complete_onboarding':
            permission_classes = [IsAuthenticated, CanCompleteOnboarding]
        elif self.action == 'update_skills':
            permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
        else:
            permission_classes = [IsAuthenticated, TenantIsolationPermission]

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return StudentProfileCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return StudentProfileUpdateSerializer
        elif self.action == 'complete_onboarding':
            return OnboardingCompleteSerializer
        elif self.action == 'update_skills':
            return SkillsUpdateSerializer
        return StudentProfileSerializer

    def get_queryset(self):
        """Filter queryset based on user role and tenant."""
        queryset = super().get_queryset()
        user = self.request.user

        # Admin users see all profiles
        if user.role == 'admin':
            return queryset

        # Students only see profiles from their own university
        if user.role == 'student' and user.university:
            return queryset.filter(university=user.university)

        # Return empty queryset if no valid tenant
        return queryset.none()

    def create(self, request, *args, **kwargs):
        """Create a new student profile."""
        # Check if profile already exists for this user
        if StudentProfile.objects.filter(user=request.user).exists():
            return Response(
                {'error': 'Profile already exists for this user.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Return full profile data
        profile = serializer.instance
        response_serializer = StudentProfileSerializer(profile)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """Update a student profile."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return full profile data
        response_serializer = StudentProfileSerializer(instance)
        return Response(response_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Delete a student profile."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'message': 'Profile deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['get'], url_path='me')
    def get_current_user_profile(self, request):
        """Get the current authenticated user's profile."""
        try:
            profile = StudentProfile.objects.select_related('user', 'career_goal').get(
                user=request.user
            )
            serializer = StudentProfileSerializer(profile)
            return Response(serializer.data)
        except StudentProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found. Please create a profile first.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], url_path='complete-onboarding')
    def complete_onboarding(self, request, pk=None):
        """Mark onboarding as completed for a profile."""
        profile = self.get_object()

        if profile.onboarding_completed:
            return Response(
                {
                    'completed': True,
                    'message': 'Onboarding already completed.'
                },
                status=status.HTTP_200_OK
            )

        # Validate that required fields are filled
        if not all([profile.university, profile.institute, profile.course, profile.program]):
            return Response(
                {
                    'error': 'Cannot complete onboarding. Required fields missing: university, institute, course, program.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        profile.complete_onboarding()

        return Response(
            {
                'completed': True,
                'message': 'Onboarding completed successfully.'
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post', 'patch'], url_path='update-skills')
    def update_skills(self, request, pk=None):
        """Update skills/interests for a profile."""
        profile = self.get_object()
        serializer = SkillsUpdateSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Return updated profile
        response_serializer = StudentProfileSerializer(profile)
        return Response(response_serializer.data)


class CareerGoalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing career goals.

    Endpoints:
    - GET /career-goals/ - List all active career goals
    - GET /career-goals/{id}/ - Retrieve a specific career goal
    """

    queryset = CareerGoal.objects.filter(is_active=True)
    serializer_class = CareerGoalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    pagination_class = None  # No pagination for career goals

    def list(self, request, *args, **kwargs):
        """List all active career goals."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific career goal."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
