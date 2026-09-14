from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from .models import KnowledgeItem, KnowledgeReport
from .serializers import (
    KnowledgeItemSerializer,
    KnowledgeItemListSerializer,
    KnowledgeItemSearchSerializer,
    KnowledgeItemCreateSerializer,
    KnowledgeReportSerializer,
    KnowledgeReportCreateSerializer,
    KnowledgeReportResolveSerializer,
)
from .permissions import (
    IsSameUniversity,
    CanManageKnowledge,
    CanReportKnowledge,
    IsAdminUser,
)
from .services import KnowledgeSearchService


KNOWLEDGE_MANAGERS = ['editor', 'institute_admin', 'university_admin', 'organizer', 'admin']


class KnowledgeItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing knowledge items.

    Endpoints:
    - GET /api/v1/knowledge/items/ - List knowledge items (filtered by university)
    - POST /api/v1/knowledge/items/ - Create knowledge item (admin only)
    - GET /api/v1/knowledge/items/{id}/ - Retrieve knowledge item
    - PUT/PATCH /api/v1/knowledge/items/{id}/ - Update knowledge item (admin only)
    - DELETE /api/v1/knowledge/items/{id}/ - Delete knowledge item (admin only)
    - POST /api/v1/knowledge/items/{id}/publish/ - Publish knowledge item (admin only)
    - POST /api/v1/knowledge/items/{id}/unpublish/ - Unpublish knowledge item (admin only)
    - POST /api/v1/knowledge/items/{id}/verify/ - Verify knowledge item (admin only)
    - POST /api/v1/knowledge/items/{id}/mark_outdated/ - Mark as outdated (admin only)
    - GET /api/v1/knowledge/items/search/ - Search knowledge items
    """

    queryset = KnowledgeItem.objects.all()
    permission_classes = [IsAuthenticated, IsSameUniversity, CanManageKnowledge]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['verified_status', 'published', 'responsible_unit']
    ordering_fields = ['created_at', 'updated_at', 'actual_until', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter queryset by user's university and visibility rules."""
        queryset = super().get_queryset()
        user = self.request.user

        # Admins see all items; editors see all items inside their tenant.
        if user.is_staff or user.is_superuser:
            university = self.request.query_params.get('university')
            if university:
                queryset = queryset.filter(university=university)
            return queryset

        if user.role in KNOWLEDGE_MANAGERS and user.university:
            return queryset.filter(university=user.university)

        # Regular users only see published items from their university
        user_university = getattr(user, 'university', None)
        if not user_university:
            return queryset.none()

        queryset = queryset.filter(
            university=user_university,
            published=True
        )

        # Filter by audience if specified
        audience = self.request.query_params.get('audience')
        if audience:
            queryset = queryset.filter(audience__contains=[audience])

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return KnowledgeItemListSerializer
        elif self.action == 'create':
            return KnowledgeItemCreateSerializer
        elif self.action == 'search':
            return KnowledgeItemSearchSerializer
        return KnowledgeItemSerializer

    def create(self, request, *args, **kwargs):
        """Create a new knowledge item."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Return full serializer
        instance = serializer.instance
        output_serializer = KnowledgeItemSerializer(instance)

        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def perform_create(self, serializer):
        serializer.save(university=self.request.user.university)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsSameUniversity])
    def search(self, request):
        """
        Search knowledge items using full-text search.
        Query parameter: q (search query)
        """
        query = request.query_params.get('q', '').strip()

        if not query:
            return Response(
                {'error': 'Search query parameter "q" is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        user_university = getattr(user, 'university', None)

        if not user_university and not user.is_staff and not user.is_superuser:
            return Response(
                {'error': 'User must belong to a university to search.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(KnowledgeSearchService().search(query, user))

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def publish(self, request, pk=None):
        """Publish a knowledge item."""
        knowledge_item = self.get_object()
        knowledge_item.publish()
        serializer = self.get_serializer(knowledge_item)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def unpublish(self, request, pk=None):
        """Unpublish a knowledge item."""
        knowledge_item = self.get_object()
        knowledge_item.unpublish()
        serializer = self.get_serializer(knowledge_item)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def verify(self, request, pk=None):
        """Verify a knowledge item."""
        knowledge_item = self.get_object()
        knowledge_item.verify()
        serializer = self.get_serializer(knowledge_item)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def mark_outdated(self, request, pk=None):
        """Mark a knowledge item as outdated."""
        knowledge_item = self.get_object()
        knowledge_item.mark_outdated()
        serializer = self.get_serializer(knowledge_item)
        return Response(serializer.data)


class KnowledgeReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing knowledge reports.

    Endpoints:
    - GET /api/v1/knowledge/reports/ - List reports (users see own, admins see all)
    - POST /api/v1/knowledge/reports/ - Create report
    - GET /api/v1/knowledge/reports/{id}/ - Retrieve report
    - POST /api/v1/knowledge/reports/{id}/resolve/ - Resolve report (admin only)
    - POST /api/v1/knowledge/reports/{id}/reject/ - Reject report (admin only)
    - POST /api/v1/knowledge/reports/{id}/start_review/ - Start reviewing (admin only)
    """

    queryset = KnowledgeReport.objects.all()
    permission_classes = [IsAuthenticated, IsSameUniversity, CanReportKnowledge]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'knowledge_item']
    ordering_fields = ['created_at', 'updated_at', 'resolved_at']
    ordering = ['-created_at']
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        user = self.request.user

        # Admins see all reports
        if user.is_staff or user.is_superuser:
            university = self.request.query_params.get('university')
            if university:
                queryset = queryset.filter(university=university)
            return queryset

        # Regular users only see their own reports from their university
        user_university = getattr(user, 'university', None)
        if not user_university:
            return queryset.none()

        return queryset.filter(
            student=user,
            university=user_university
        )

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return KnowledgeReportCreateSerializer
        elif self.action in ['resolve', 'reject']:
            return KnowledgeReportResolveSerializer
        return KnowledgeReportSerializer

    def create(self, request, *args, **kwargs):
        """Create a new knowledge report."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Return full serializer
        instance = serializer.instance
        output_serializer = KnowledgeReportSerializer(instance)

        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def resolve(self, request, pk=None):
        """Resolve a knowledge report."""
        report = self.get_object()

        if report.status in ['resolved', 'rejected']:
            return Response(
                {'error': 'Report has already been resolved or rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = KnowledgeReportResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resolution_note = serializer.validated_data.get('resolution_note', '')
        report.resolve(resolved_by=request.user, resolution_note=resolution_note)

        output_serializer = KnowledgeReportSerializer(report)
        return Response(output_serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def reject(self, request, pk=None):
        """Reject a knowledge report."""
        report = self.get_object()

        if report.status in ['resolved', 'rejected']:
            return Response(
                {'error': 'Report has already been resolved or rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = KnowledgeReportResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resolution_note = serializer.validated_data.get('resolution_note', '')
        report.reject(resolved_by=request.user, resolution_note=resolution_note)

        output_serializer = KnowledgeReportSerializer(report)
        return Response(output_serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def start_review(self, request, pk=None):
        """Mark report as under review."""
        report = self.get_object()

        if report.status != 'pending':
            return Response(
                {'error': 'Only pending reports can be marked as under review.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        report.start_review()
        serializer = KnowledgeReportSerializer(report)
        return Response(serializer.data)
