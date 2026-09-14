from django.contrib import admin
from .models import StudentProfile, CareerGoal


@admin.register(CareerGoal)
class CareerGoalAdmin(admin.ModelAdmin):
    """Admin interface for CareerGoal model."""

    list_display = ['name', 'is_active', 'student_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def student_count(self, obj):
        """Display count of students with this career goal."""
        return obj.students.count()
    student_count.short_description = 'Students'


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Admin interface for StudentProfile model."""

    list_display = [
        'user',
        'university',
        'institute',
        'course',
        'career_goal',
        'onboarding_completed',
        'created_at'
    ]
    list_filter = [
        'onboarding_completed',
        'university',
        'course',
        'career_goal',
        'created_at'
    ]
    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'university',
        'institute',
        'program'
    ]
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['career_goal']
    ordering = ['-created_at']

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Academic Information', {
            'fields': ('university', 'institute', 'course', 'program')
        }),
        ('Interests & Goals', {
            'fields': ('interests', 'career_goal')
        }),
        ('Onboarding', {
            'fields': ('onboarding_completed',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'career_goal')

    actions = ['mark_onboarding_completed', 'mark_onboarding_pending']

    def mark_onboarding_completed(self, request, queryset):
        """Mark selected profiles as having completed onboarding."""
        updated = queryset.update(onboarding_completed=True)
        self.message_user(
            request,
            f'{updated} profile(s) marked as onboarding completed.'
        )
    mark_onboarding_completed.short_description = 'Mark onboarding as completed'

    def mark_onboarding_pending(self, request, queryset):
        """Mark selected profiles as pending onboarding."""
        updated = queryset.update(onboarding_completed=False)
        self.message_user(
            request,
            f'{updated} profile(s) marked as onboarding pending.'
        )
    mark_onboarding_pending.short_description = 'Mark onboarding as pending'
