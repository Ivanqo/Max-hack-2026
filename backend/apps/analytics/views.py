from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q, Max, Min
from django.utils import timezone
from datetime import timedelta
from .models import InteractionEvent, AuditLog
from .serializers import (
    InteractionEventSerializer,
    AuditLogSerializer,
    TopQuerySerializer,
    UnansweredQuerySerializer,
    OverviewStatsSerializer,
    EventTypeCountSerializer,
    EntityTypeCountSerializer
)
from .permissions import CanViewAnalytics, get_user_university


class InteractionEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing interaction events.
    Supports listing, creating, and viewing interaction events with tenant isolation.
    """

    serializer_class = InteractionEventSerializer
    permission_classes = [CanViewAnalytics]
    filterset_fields = ['event_type', 'entity_type', 'user']
    search_fields = ['event_type', 'entity_type', 'entity_id']
    ordering_fields = ['created_at', 'event_type']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter queryset to only include events from user's university."""
        university = get_user_university(self.request.user)
        if not university:
            return InteractionEvent.objects.none()
        return InteractionEvent.objects.filter(university=university).select_related('user')

    def perform_create(self, serializer):
        """Set university from authenticated user when creating events."""
        university = get_user_university(self.request.user)
        if not university:
            return Response(
                {"error": "User must belong to a university to create events."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save(university=university)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs.
    Read-only access for admins to review administrative actions with tenant isolation.
    """

    serializer_class = AuditLogSerializer
    permission_classes = [CanViewAnalytics]
    filterset_fields = ['action', 'entity_type', 'admin']
    search_fields = ['action', 'entity_type', 'entity_id']
    ordering_fields = ['timestamp', 'action']
    ordering = ['-timestamp']

    def get_queryset(self):
        """Filter queryset to only include logs from user's university."""
        university = get_user_university(self.request.user)
        if not university:
            return AuditLog.objects.none()
        return AuditLog.objects.filter(university=university).select_related('admin')


class TopQueriesView(APIView):
    """
    API view to get top search queries with tenant isolation.
    Returns most frequent search terms within the user's university.
    """

    permission_classes = [CanViewAnalytics]

    def get(self, request):
        """Get top search queries."""
        university = get_user_university(request.user)
        if not university:
            return Response(
                {"error": "User must belong to a university."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get time range from query params (default: last 30 days)
        days = int(request.query_params.get('days', 30))
        limit = int(request.query_params.get('limit', 20))

        start_date = timezone.now() - timedelta(days=days)

        # Get search events with queries
        search_events = InteractionEvent.objects.filter(
            university=university,
            event_type='search',
            created_at__gte=start_date,
            metadata__isnull=False
        )

        # Extract and aggregate queries
        query_stats = {}
        for event in search_events:
            query = event.metadata.get('query', '').strip().lower()
            if query:
                if query not in query_stats:
                    query_stats[query] = {
                        'query': query,
                        'count': 0,
                        'last_searched': event.created_at
                    }
                query_stats[query]['count'] += 1
                if event.created_at > query_stats[query]['last_searched']:
                    query_stats[query]['last_searched'] = event.created_at

        # Sort by count and get top queries
        top_queries = sorted(query_stats.values(), key=lambda x: x['count'], reverse=True)[:limit]

        serializer = TopQuerySerializer(top_queries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UnansweredQueriesView(APIView):
    """
    API view to get unanswered search queries with tenant isolation.
    Returns searches that potentially yielded no or poor results.
    """

    permission_classes = [CanViewAnalytics]

    def get(self, request):
        """Get unanswered queries."""
        university = get_user_university(request.user)
        if not university:
            return Response(
                {"error": "User must belong to a university."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get time range from query params (default: last 30 days)
        days = int(request.query_params.get('days', 30))
        limit = int(request.query_params.get('limit', 20))

        start_date = timezone.now() - timedelta(days=days)

        # Get search events marked as having no results
        search_events = InteractionEvent.objects.filter(
            university=university,
            event_type='search',
            created_at__gte=start_date,
            metadata__has_key='no_results'
        ).filter(
            Q(metadata__no_results=True) | Q(metadata__result_count=0)
        )

        # Extract and aggregate unanswered queries
        query_stats = {}
        for event in search_events:
            query = event.metadata.get('query', '').strip().lower()
            if query:
                if query not in query_stats:
                    query_stats[query] = {
                        'query': query,
                        'count': 0,
                        'first_searched': event.created_at,
                        'last_searched': event.created_at
                    }
                query_stats[query]['count'] += 1
                if event.created_at < query_stats[query]['first_searched']:
                    query_stats[query]['first_searched'] = event.created_at
                if event.created_at > query_stats[query]['last_searched']:
                    query_stats[query]['last_searched'] = event.created_at

        # Sort by count and get top unanswered queries
        unanswered_queries = sorted(query_stats.values(), key=lambda x: x['count'], reverse=True)[:limit]

        serializer = UnansweredQuerySerializer(unanswered_queries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OverviewAnalyticsView(APIView):
    """
    API view to get overview analytics with tenant isolation.
    Returns comprehensive statistics about user interactions.
    """

    permission_classes = [CanViewAnalytics]

    def get(self, request):
        """Get overview analytics."""
        university = get_user_university(request.user)
        if not university:
            return Response(
                {"error": "User must belong to a university."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get time range from query params (default: last 30 days)
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        end_date = timezone.now()

        # Base queryset for the university and time range
        base_qs = InteractionEvent.objects.filter(
            university=university,
            created_at__gte=start_date,
            created_at__lte=end_date
        )

        # Total interactions
        total_interactions = base_qs.count()

        # Unique users
        total_users = base_qs.exclude(user__isnull=True).values('user').distinct().count()

        # Event type counts
        total_searches = base_qs.filter(event_type='search').count()
        total_views = base_qs.filter(event_type='view').count()
        total_clicks = base_qs.filter(event_type='click').count()
        total_saves = base_qs.filter(event_type='save').count()
        total_applies = base_qs.filter(event_type='apply').count()

        # Active users by time period
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = timezone.now() - timedelta(days=7)
        month_start = timezone.now() - timedelta(days=30)

        active_users_today = base_qs.filter(
            created_at__gte=today_start
        ).exclude(user__isnull=True).values('user').distinct().count()

        active_users_week = base_qs.filter(
            created_at__gte=week_start
        ).exclude(user__isnull=True).values('user').distinct().count()

        active_users_month = base_qs.filter(
            created_at__gte=month_start
        ).exclude(user__isnull=True).values('user').distinct().count()

        # Popular entity types
        entity_type_stats = base_qs.exclude(
            entity_type__isnull=True
        ).values('entity_type').annotate(
            count=Count('id')
        ).order_by('-count')

        popular_entity_types = {
            item['entity_type']: item['count']
            for item in entity_type_stats
        }

        # Event type distribution
        event_type_stats = base_qs.values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')

        event_type_distribution = {
            item['event_type']: item['count']
            for item in event_type_stats
        }

        # Compile stats
        stats = {
            'total_interactions': total_interactions,
            'total_users': total_users,
            'total_searches': total_searches,
            'total_views': total_views,
            'total_clicks': total_clicks,
            'total_saves': total_saves,
            'total_applies': total_applies,
            'active_users_today': active_users_today,
            'active_users_week': active_users_week,
            'active_users_month': active_users_month,
            'popular_entity_types': popular_entity_types,
            'event_type_distribution': event_type_distribution,
            'time_range_start': start_date,
            'time_range_end': end_date
        }

        serializer = OverviewStatsSerializer(stats)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HealthCheckView(APIView):
    """
    Health check endpoint for monitoring.
    No authentication required.
    """

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        """Return health status."""
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'service': 'analytics-api'
        }, status=status.HTTP_200_OK)
