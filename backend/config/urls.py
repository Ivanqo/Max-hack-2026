"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts.views import (
    ChangePasswordView,
    CustomTokenObtainPairView,
    HealthCheckView,
    UserProfileView,
    UserRegistrationView,
)
from apps.notifications.max_views import MaxLaunchView, MaxWebhookView
from . import mvp_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', mvp_views.root_health, name='root_health'),
    path('api/health/', HealthCheckView.as_view(), name='health_check'),
    path('api/universities', mvp_views.universities, name='mvp_universities'),
    path('api/institutes', mvp_views.institutes, name='mvp_institutes'),
    path('api/interests', mvp_views.interests, name='mvp_interests'),
    path('api/skills', mvp_views.skills, name='mvp_skills'),
    path('api/programs', mvp_views.programs, name='mvp_programs'),
    path('api/onboarding', mvp_views.onboarding, name='mvp_onboarding'),
    path('api/auth/register/', UserRegistrationView.as_view(), name='auth_register_alias'),
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='auth_login_alias'),
    path('api/auth/profile/', UserProfileView.as_view(), name='auth_profile_alias'),
    path('api/auth/change-password/', ChangePasswordView.as_view(), name='auth_change_password_alias'),
    path('api/max/launch/', MaxLaunchView.as_view(), name='max_launch'),
    path('api/max/webhook/', MaxWebhookView.as_view(), name='max_webhook'),
    path('api/courses', mvp_views.courses, name='mvp_courses'),
    path('api/courses/<int:course_id>', mvp_views.course_detail, name='mvp_course_detail'),
    path('api/courses/<int:course_id>/enroll', mvp_views.enroll_course, name='mvp_enroll_course'),
    path('api/enrollments', mvp_views.enrollments, name='mvp_enrollments'),
    path('api/quizzes/<int:quiz_id>', mvp_views.quiz_detail, name='mvp_quiz_detail'),
    path('api/quizzes/<int:quiz_id>/submit', mvp_views.submit_quiz, name='mvp_submit_quiz'),
    path('api/admin/analytics', mvp_views.admin_analytics, name='mvp_admin_analytics'),
    path('api/opportunities', mvp_views.opportunities, name='mvp_opportunities'),
    path('api/student/career-gps', mvp_views.student_career_gps, name='mvp_student_career_gps'),
    path('api/student/profile', mvp_views.student_profile, name='mvp_student_profile'),
    path('api/student/opportunities', mvp_views.student_opportunities, name='mvp_student_opportunities'),
    path('api/student/opportunities/<int:pk>', mvp_views.student_opportunity_detail, name='mvp_student_opportunity_detail'),
    path('api/student/opportunities/<int:pk>/save', mvp_views.student_save_opportunity, name='mvp_student_save_opportunity'),
    path('api/student/subscriptions', mvp_views.student_subscriptions, name='mvp_student_subscriptions'),
    path('api/career/goals', mvp_views.student_career_goals, name='mvp_student_career_goals'),
    path('api/career/analysis/<int:role_id>', mvp_views.student_career_analysis, name='mvp_student_career_analysis'),
    path('api/admin/opportunities', mvp_views.admin_opportunities, name='mvp_admin_opportunities'),
    path('api/admin/opportunities/<int:pk>', mvp_views.admin_opportunity_detail, name='mvp_admin_opportunity_detail'),
    path('api/career-roles', mvp_views.career_roles, name='mvp_career_roles'),
    path('api/admin/career-roles', mvp_views.admin_career_roles, name='mvp_admin_career_roles'),
    path('api/admin/career-roles/<int:pk>', mvp_views.admin_career_role_detail, name='mvp_admin_career_role_detail'),
    path('api/knowledge', mvp_views.knowledge, name='mvp_knowledge'),
    path('api/knowledge/search', mvp_views.knowledge_search, name='mvp_knowledge_search'),
    path('api/knowledge/<int:pk>', mvp_views.knowledge_detail, name='mvp_knowledge_detail'),
    path('api/admin/knowledge', mvp_views.admin_knowledge, name='mvp_admin_knowledge'),
    path('api/admin/knowledge/<int:pk>', mvp_views.admin_knowledge_detail, name='mvp_admin_knowledge_detail'),
    path('api/v1/accounts/', include('apps.accounts.urls')),
    path('api/v1/careers/', include('apps.careers.urls')),
    path('api/v1/opportunities/', include('apps.opportunities.urls')),
    path('api/v1/', include('apps.profiles.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
    path('api/v1/knowledge/', include('apps.knowledge.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/subscriptions/', include('apps.subscriptions.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
