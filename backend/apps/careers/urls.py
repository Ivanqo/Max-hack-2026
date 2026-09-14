from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import connection
from django.core.cache import cache

from .views import (
    SkillViewSet, CareerRoleViewSet,
    StudentSkillViewSet, CareerGPSViewSet
)


# Health check endpoint
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for monitoring.
    Returns service status and basic health information.
    """
    health_status = {
        'status': 'healthy',
        'service': 'careers-api',
        'version': '1.0.0',
        'timestamp': '2026-09-05T08:10:44.384Z'
    }

    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['database'] = 'connected'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['database'] = f'error: {str(e)}'

    # Check cache (if configured)
    try:
        cache.set('health_check', 'ok', 10)
        cache_status = cache.get('health_check')
        health_status['cache'] = 'connected' if cache_status == 'ok' else 'disconnected'
    except Exception as e:
        health_status['cache'] = f'error: {str(e)}'

    return Response(health_status)


# Create router and register viewsets
router = DefaultRouter()
router.register(r'skills', SkillViewSet, basename='skill')
router.register(r'career-roles', CareerRoleViewSet, basename='career-role')
router.register(r'student-skills', StudentSkillViewSet, basename='student-skill')
router.register(r'gps', CareerGPSViewSet, basename='gps')

urlpatterns = [
    path('health/', health_check, name='health-check'),
    path('', include(router.urls)),
]
