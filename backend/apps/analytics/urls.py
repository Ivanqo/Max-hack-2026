from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InteractionEventViewSet,
    AuditLogViewSet,
    TopQueriesView,
    UnansweredQueriesView,
    OverviewAnalyticsView,
    HealthCheckView
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'events', InteractionEventViewSet, basename='interaction-event')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

# URL patterns
urlpatterns = [
    # ViewSet routes (events and audit logs)
    path('', include(router.urls)),

    # Admin analytics endpoints
    path('admin/top-queries/', TopQueriesView.as_view(), name='top-queries'),
    path('admin/unanswered-queries/', UnansweredQueriesView.as_view(), name='unanswered-queries'),
    path('admin/overview/', OverviewAnalyticsView.as_view(), name='overview-analytics'),

    # Health check endpoint
    path('health/', HealthCheckView.as_view(), name='health-check'),
]
