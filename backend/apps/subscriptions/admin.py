from django.contrib import admin
from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """
    Admin interface for managing student subscriptions.
    """
    list_display = [
        'id',
        'student',
        'topic',
        'active',
        'created_at',
        'updated_at'
    ]
    list_filter = [
        'active',
        'topic',
        'created_at'
    ]
    search_fields = [
        'student__username',
        'student__email',
        'topic'
    ]
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    fieldsets = (
        ('Student Information', {
            'fields': ('student',)
        }),
        ('Subscription Details', {
            'fields': ('topic', 'filters', 'active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'created_at'
    list_per_page = 25

    def get_queryset(self, request):
        """
        Optimize queryset with related student data.
        """
        qs = super().get_queryset(request)
        return qs.select_related('student')
