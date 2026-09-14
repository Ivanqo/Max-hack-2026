from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import Skill, CareerRole, CareerRoleSkill, StudentSkill
from .serializers import (
    SkillSerializer, CareerRoleSerializer, CareerRoleListSerializer,
    CareerRoleSkillSerializer, StudentSkillSerializer,
    CareerMatchSerializer, GPSCalculationSerializer, GPSResultSerializer
)
from .permissions import (
    IsSameUniversity, IsOrganizerOrAdmin,
    IsStudentOrReadOnly, IsOwnerOrAdmin
)
from .services import CareerGPSService


CAREER_MANAGERS = ['editor', 'institute_admin', 'university_admin', 'organizer', 'admin']


class SkillViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing skills.

    Endpoints:
    - GET /skills/ - List all skills (filtered by university)
    - POST /skills/ - Create new skill (organizers/admins only)
    - GET /skills/{id}/ - Retrieve specific skill
    - PUT/PATCH /skills/{id}/ - Update skill (organizers/admins only)
    - DELETE /skills/{id}/ - Delete skill (organizers/admins only)
    - GET /skills/by_category/ - List skills grouped by category
    """
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated, IsSameUniversity, IsOrganizerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'university']
    search_fields = ['name', 'category']
    ordering_fields = ['name', 'category', 'created_at']
    ordering = ['category', 'name']

    def get_queryset(self):
        """Filter skills by user's university or general skills."""
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser or user.role in ['admin', 'university_admin']:
            return queryset

        # Filter by user's university or general skills (university=None)
        university = getattr(user, 'university', None)
        if university:
            queryset = queryset.filter(
                Q(university=university) | Q(university__isnull=True)
            )

        return queryset

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get skills grouped by category."""
        queryset = self.filter_queryset(self.get_queryset())

        categories = {}
        for skill in queryset:
            category = skill.get_category_display()
            if category not in categories:
                categories[category] = []
            categories[category].append(SkillSerializer(skill).data)

        return Response({
            'categories': categories,
            'total_skills': queryset.count()
        })


class CareerRoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing career roles.

    Endpoints:
    - GET /career-roles/ - List all career roles (filtered by university)
    - POST /career-roles/ - Create new career role (organizers/admins only)
    - GET /career-roles/{id}/ - Retrieve specific career role
    - PUT/PATCH /career-roles/{id}/ - Update career role (organizers/admins only)
    - DELETE /career-roles/{id}/ - Delete career role (organizers/admins only)
    - POST /career-roles/{id}/add_skill/ - Add required skill to role
    - DELETE /career-roles/{id}/remove_skill/ - Remove required skill from role
    """
    queryset = CareerRole.objects.prefetch_related(
        'required_skills__skill'
    ).all()
    permission_classes = [IsAuthenticated, IsSameUniversity, IsOrganizerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['active', 'university']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']

    def get_serializer_class(self):
        """Use lightweight serializer for list action."""
        if self.action == 'list':
            return CareerRoleListSerializer
        return CareerRoleSerializer

    def get_queryset(self):
        """Filter career roles by user's university."""
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        # Filter by user's university
        university = getattr(user, 'university', None)
        if university:
            queryset = queryset.filter(university=university)

        # Only show active roles to students
        if user.role == 'student':
            queryset = queryset.filter(active=True)

        return queryset

    @action(detail=True, methods=['post'])
    def add_skill(self, request, pk=None):
        """Add a required skill to a career role."""
        career_role = self.get_object()

        serializer = CareerRoleSkillSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            # Check if this skill already exists for this role
            skill_id = serializer.validated_data['skill'].id
            if CareerRoleSkill.objects.filter(
                career_role=career_role,
                skill_id=skill_id
            ).exists():
                return Response(
                    {'error': 'This skill is already required for this role'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer.save(career_role=career_role)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def remove_skill(self, request, pk=None):
        """Remove a required skill from a career role."""
        career_role = self.get_object()
        skill_id = request.data.get('skill_id')

        if not skill_id:
            return Response(
                {'error': 'skill_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            role_skill = CareerRoleSkill.objects.get(
                career_role=career_role,
                skill_id=skill_id
            )
            role_skill.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CareerRoleSkill.DoesNotExist:
            return Response(
                {'error': 'Skill not found in this career role'},
                status=status.HTTP_404_NOT_FOUND
            )


class StudentSkillViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing student skills.

    Endpoints:
    - GET /student-skills/ - List student skills
    - POST /student-skills/ - Add new skill to student profile
    - GET /student-skills/{id}/ - Retrieve specific student skill
    - PUT/PATCH /student-skills/{id}/ - Update student skill
    - DELETE /student-skills/{id}/ - Remove skill from student profile
    - POST /student-skills/{id}/verify/ - Verify student skill (organizers/admins only)
    """
    queryset = StudentSkill.objects.select_related(
        'student__user', 'skill'
    ).all()
    serializer_class = StudentSkillSerializer
    permission_classes = [IsAuthenticated, IsStudentOrReadOnly, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['verified', 'level', 'skill__category']
    search_fields = ['skill__name', 'student__user__email']
    ordering_fields = ['level', 'created_at', 'updated_at']
    ordering = ['-level', 'skill__name']

    def get_queryset(self):
        """Filter student skills based on user role."""
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        # Admins and organizers see all skills in their university
        if user.role in CAREER_MANAGERS:
            university = getattr(user, 'university', None)
            if university:
                queryset = queryset.filter(
                    student__user__university=university
                )
            return queryset

        # Students see only their own skills
        if user.role == 'student':
            if hasattr(user, 'student_profile'):
                queryset = queryset.filter(student=user.student_profile)
            else:
                queryset = queryset.none()

        return queryset

    def perform_create(self, serializer):
        """Set the student to the current user's profile."""
        if hasattr(self.request.user, 'student_profile'):
            serializer.save(student=self.request.user.student_profile)
        else:
            raise ValueError("User does not have a student profile")

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a student's skill (organizers/admins only)."""
        student_skill = self.get_object()

        # Check permission
        if request.user.role not in ['organizer', 'admin'] and not request.user.is_superuser:
            return Response(
                {'error': 'Only organizers and admins can verify skills'},
                status=status.HTTP_403_FORBIDDEN
            )

        student_skill.verified = True
        student_skill.save(update_fields=['verified', 'updated_at'])

        serializer = self.get_serializer(student_skill)
        return Response(serializer.data)


class CareerGPSViewSet(viewsets.ViewSet):
    """
    ViewSet for GPS (Goal Progress Score) calculations.

    Endpoints:
    - POST /gps/calculate/ - Calculate GPS for current user or specified student
    - GET /gps/matches/ - Get career role matches for current user
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """
        Calculate GPS (Goal Progress Score) for a student.

        The GPS represents how well a student's skills match available career roles.
        Returns overall score and top matching roles.
        """
        serializer = GPSCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Determine which student to calculate for
        student_id = serializer.validated_data.get('student_id')

        if student_id:
            # Admins/organizers can calculate for any student in their university
            if request.user.role not in CAREER_MANAGERS and not request.user.is_superuser:
                return Response(
                    {'error': 'Only admins and organizers can calculate GPS for other students'},
                    status=status.HTTP_403_FORBIDDEN
                )

            from apps.profiles.models import StudentProfile
            try:
                student_profile = StudentProfile.objects.select_related('user').get(
                    user_id=student_id
                )

                # Check university match
                if not request.user.is_superuser:
                    if student_profile.user.university != request.user.university:
                        return Response(
                            {'error': 'Cannot access students from other universities'},
                            status=status.HTTP_403_FORBIDDEN
                        )
            except StudentProfile.DoesNotExist:
                return Response(
                    {'error': 'Student profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Calculate for current user
            if not hasattr(request.user, 'student_profile'):
                return Response(
                    {'error': 'User does not have a student profile'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            student_profile = request.user.student_profile

        career_role = self._select_career_role(
            student_profile,
            serializer.validated_data.get('career_role_id')
        )
        if not career_role:
            return Response(
                {'error': 'Career role not found for this student university.'},
                status=status.HTTP_404_NOT_FOUND
            )

        result = CareerGPSService().calculate(student_profile, career_role)
        result['student_id'] = student_profile.user.id
        result['student_email'] = student_profile.user.email
        result['calculated_at'] = timezone.now()
        return Response(result)

    @action(detail=False, methods=['get'])
    def matches(self, request):
        """Get career role matches for the current user."""
        if not hasattr(request.user, 'student_profile'):
            return Response(
                {'error': 'User does not have a student profile'},
                status=status.HTTP_400_BAD_REQUEST
            )

        student_profile = request.user.student_profile

        # Get all active career roles for the student's university
        career_roles = CareerRole.objects.filter(
            university=student_profile.user.university,
            active=True
        ).prefetch_related('required_skills__skill')

        service = CareerGPSService()
        matches = []
        for role in career_roles:
            result = service.calculate(student_profile, role)
            matches.append({
                'career_role_id': role.id,
                'career_role_name': role.name,
                'match_score': result['readiness_score'],
                'required_skills_count': role.required_skills.count(),
                'matched_skills_count': len(result['strengths']),
                'university': role.university
            })

        # Sort by match score descending
        matches.sort(key=lambda x: x['match_score'], reverse=True)

        serializer = CareerMatchSerializer(matches, many=True)
        return Response({
            'matches': serializer.data,
            'total_matches': len(matches)
        })

    def _select_career_role(self, student_profile, career_role_id=None):
        queryset = CareerRole.objects.filter(
            university=student_profile.user.university,
            active=True
        ).prefetch_related('required_skills__skill')
        if career_role_id:
            return queryset.filter(id=career_role_id).first()
        if student_profile.career_goal:
            role = queryset.filter(name__iexact=student_profile.career_goal.name).first()
            if role:
                return role
        return queryset.first()
