from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OpportunityViewSet, SavedOpportunityViewSet

app_name = 'opportunities'

router = DefaultRouter()
router.register(r'', OpportunityViewSet, basename='opportunity')
router.register(r'saved', SavedOpportunityViewSet, basename='saved-opportunity')

urlpatterns = [
    path('', include(router.urls)),
]
