from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import KnowledgeItemViewSet, KnowledgeReportViewSet

app_name = 'knowledge'

router = DefaultRouter()
router.register(r'items', KnowledgeItemViewSet, basename='knowledge-item')
router.register(r'reports', KnowledgeReportViewSet, basename='knowledge-report')

urlpatterns = [
    path('', include(router.urls)),
]
