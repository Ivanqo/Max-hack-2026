from django.contrib import admin
from .models import InteractionEvent, AuditLog


@admin.register(InteractionEvent)
class InteractionEventAdmin(admin.ModelAdmin):
    """Admin interface for InteractionEvent model."""

    list_display = [
        'id',
        'university',
        'user',
        'event_type',
        'entity_type',
        'entity_id',
        'created_at',
    ]
    list_filter = [
        'event_type',
        'entity_type',
        'university',
        'created_at',
    ]
    search_fields = [
        'university',
        'user__email',
        'entity_id',
        'metadata',
    ]
    readonly_fields = [
        'created_at',
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50

    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'entity_type', 'entity_id')
        }),
        ('Context', {
            'fields': ('university', 'user')
        }),
        ('Data', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )

    def has_add_permission(self, request):
        """Disable manual creation of events through admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make events read-only in admin."""
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog model."""

    list_display = [
        'id',
        'university',
        'admin',
        'action',
        'entity_type',
        'entity_id',
        'timestamp',
    ]
    list_filter = [
        'action',
        'entity_type',
        'university',
        'timestamp',
    ]
    search_fields = [
        'university',
        'admin__email',
        'entity_id',
        'metadata',
    ]
    readonly_fields = [
        'timestamp',
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    list_per_page = 50

    fieldsets = (
        ('Action Information', {
            'fields': ('action', 'entity_type', 'entity_id')
        }),
        ('Context', {
            'fields': ('university', 'admin')
        }),
        ('Data', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('timestamp',)
        }),
    )

    def has_add_permission(self, request):
        """Disable manual creation of audit logs through admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make audit logs read-only in admin."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs."""
        return False
