from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentProfileViewSet, CareerGoalViewSet

app_name = 'profiles'

router = DefaultRouter()
router.register(r'profiles', StudentProfileViewSet, basename='studentprofile')
router.register(r'career-goals', CareerGoalViewSet, basename='careergoal')

urlpatterns = [
    path('', include(router.urls)),
]
