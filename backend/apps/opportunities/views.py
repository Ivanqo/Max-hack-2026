from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Count, Prefetch
from django_filters.rest_framework import DjangoFilterBackend

from .models import Opportunity, SavedOpportunity, MatchResult
from .serializers import (
    OpportunityListSerializer,
    OpportunityDetailSerializer,
    OpportunityCreateUpdateSerializer,
    SavedOpportunitySerializer,
    MatchResultSerializer
)
from .permissions import (
    CanManageOpportunity,
    IsSameUniversityOrAdmin,
    CanVerifyOpportunity,
    IsStudent
)
from .services import OpportunityMatchingService
from apps.analytics.models import AuditLog, InteractionEvent
from apps.notifications.services import get_notification_service


TENANT_ADMINS = ['admin', 'university_admin']


class OpportunityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing opportunities.

    Provides CRUD operations with proper RBAC and tenant isolation.

    list: Get all opportunities (filtered by university for non-admins)
    retrieve: Get a single opportunity
    create: Create a new opportunity (mentor/organizer/admin only)
    update: Update an opportunity (owner/organizer/admin only)
    partial_update: Partially update an opportunity
    destroy: Delete an opportunity (owner/organizer/admin only)
    matches: Get opportunities with match scores for current user
    verify: Verify an opportunity (organizer/admin only)
    publish: Publish/unpublish an opportunity
    """

    queryset = Opportunity.objects.select_related('created_by').prefetch_related('required_skills')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'verified_status', 'published']
    search_fields = ['title', 'description', 'requirements']
    ordering_fields = ['created_at', 'updated_at', 'deadline', 'title']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return OpportunityDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return OpportunityCreateUpdateSerializer
        return OpportunityListSerializer

    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action in ['verify']:
            permission_classes = [IsAuthenticated, CanVerifyOpportunity]
        elif self.action in ['create', 'update', 'partial_update', 'destroy', 'publish']:
            permission_classes = [IsAuthenticated, CanManageOpportunity]
        else:
            permission_classes = [IsAuthenticated, IsSameUniversityOrAdmin]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filter queryset based on user role and university (tenant isolation).
        """
        queryset = super().get_queryset()
        user = self.request.user

        # Admins see all opportunities
        if user.role in TENANT_ADMINS:
            return queryset

        # Filter by user's university for tenant isolation
        queryset = queryset.filter(university=user.university)

        # Students only see published and verified opportunities
        if user.role == 'student':
            queryset = queryset.filter(published=True, verified_status='verified')

        return queryset

    def perform_create(self, serializer):
        """Set ownership, tenant, audit, and subscription notifications."""
        opportunity = serializer.save(
            created_by=self.request.user,
            university=self.request.user.university,
        )
        self._audit('create', opportunity)
        if opportunity.published and opportunity.verified_status == 'verified':
            get_notification_service().create_for_opportunity_subscriptions(opportunity)

    def perform_update(self, serializer):
        was_publishable = serializer.instance.published and serializer.instance.verified_status == 'verified'
        opportunity = serializer.save()
        self._audit('update', opportunity)
        is_publishable = opportunity.published and opportunity.verified_status == 'verified'
        if is_publishable and not was_publishable:
            get_notification_service().create_for_opportunity_subscriptions(opportunity)

    @action(detail=False, methods=['get'], url_path='matches')
    def matches(self, request):
        """
        Get opportunities with match scores for the current user.
        Returns opportunities sorted by match score.
        """
        if request.user.role != 'student':
            return Response(
                {'detail': 'Only students can view matches.'},
                status=status.HTTP_403_FORBIDDEN
            )

        opportunities = self.filter_queryset(self.get_queryset())
        min_score = int(request.query_params.get('min_score', 0))
        service = OpportunityMatchingService()
        for opportunity, result in service.rank_for_user(request.user, opportunities):
            if result['score'] < min_score:
                continue

        matches = MatchResult.objects.filter(
            student=request.user,
            opportunity__in=opportunities,
            score__gte=min_score,
        ).select_related('opportunity', 'opportunity__created_by').prefetch_related(
            'opportunity__required_skills'
        ).order_by('-score')

        # Apply pagination
        page = self.paginate_queryset(matches)
        if page is not None:
            serializer = MatchResultSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = MatchResultSerializer(matches, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='verify')
    def verify(self, request, pk=None):
        """
        Verify or reject an opportunity.

        Body: {"status": "verified"} or {"status": "rejected"}
        """
        opportunity = self.get_object()
        new_status = request.data.get('status')

        if new_status not in ['verified', 'rejected']:
            return Response(
                {'detail': 'Status must be "verified" or "rejected".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        opportunity.verified_status = new_status
        opportunity.save(update_fields=['verified_status', 'updated_at'])
        self._audit('verify' if new_status == 'verified' else 'reject', opportunity)
        if opportunity.published and new_status == 'verified':
            get_notification_service().create_for_opportunity_subscriptions(opportunity)

        serializer = self.get_serializer(opportunity)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        """
        Publish or unpublish an opportunity.

        Body: {"published": true} or {"published": false}
        """
        opportunity = self.get_object()
        published = request.data.get('published')

        if not isinstance(published, bool):
            return Response(
                {'detail': 'Published must be a boolean.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        opportunity.published = published
        opportunity.save(update_fields=['published', 'updated_at'])
        self._audit('publish' if published else 'unpublish', opportunity)
        if published and opportunity.verified_status == 'verified':
            get_notification_service().create_for_opportunity_subscriptions(opportunity)

        serializer = self.get_serializer(opportunity)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], url_path='save')
    def save_opportunity(self, request, pk=None):
        """
        Save or unsave an opportunity for the current user.

        POST: Save the opportunity
        DELETE: Unsave the opportunity
        """
        if request.user.role != 'student':
            return Response(
                {'detail': 'Only students can save opportunities.'},
                status=status.HTTP_403_FORBIDDEN
            )

        opportunity = self.get_object()

        if request.method == 'POST':
            # Check if already saved
            saved, created = SavedOpportunity.objects.get_or_create(
                student=request.user,
                opportunity=opportunity
            )
            InteractionEvent.objects.create(
                university=request.user.university,
                user=request.user,
                event_type='opportunity_save',
                entity_type='opportunity',
                entity_id=str(opportunity.id),
            )

            if not created:
                return Response(
                    {'detail': 'Opportunity already saved.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = SavedOpportunitySerializer(saved, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            deleted_count, _ = SavedOpportunity.objects.filter(
                student=request.user,
                opportunity=opportunity
            ).delete()

            if deleted_count == 0:
                return Response(
                    {'detail': 'Opportunity was not saved.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        if request.user.is_authenticated:
            InteractionEvent.objects.create(
                university=request.user.university,
                user=request.user,
                event_type='opportunity_open',
                entity_type='opportunity',
                entity_id=str(kwargs.get('pk')),
            )
        return response

    def _audit(self, action, opportunity):
        AuditLog.objects.create(
            university=opportunity.university,
            admin=self.request.user,
            action=action,
            entity_type='opportunity',
            entity_id=str(opportunity.id),
            metadata={'title': opportunity.title},
        )


class SavedOpportunityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing saved opportunities.

    list: Get all saved opportunities for the current user
    retrieve: Get a single saved opportunity
    """

    serializer_class = SavedOpportunitySerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        """Return saved opportunities for the current user only."""
        return SavedOpportunity.objects.filter(
            student=self.request.user
        ).select_related('opportunity', 'opportunity__created_by').prefetch_related(
            'opportunity__required_skills'
        ).order_by('-created_at')
