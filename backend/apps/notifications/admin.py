from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for Notification model.
    """

    list_display = [
        'id',
        'title',
        'student',
        'opportunity',
        'status_badge',
        'created_at',
        'sent_at',
    ]

    list_filter = [
        'status',
        'created_at',
        'sent_at',
    ]

    search_fields = [
        'title',
        'message',
        'student__first_name',
        'student__last_name',
        'student__email',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'sent_at',
    ]

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('id', 'student', 'title', 'message')
        }),
        (_('Related Data'), {
            'fields': ('opportunity',)
        }),
        (_('Status'), {
            'fields': ('status', 'created_at', 'sent_at')
        }),
    )

    autocomplete_fields = ['student', 'opportunity']

    list_per_page = 50

    date_hierarchy = 'created_at'

    actions = ['mark_as_sent', 'mark_as_failed', 'mark_as_pending']

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'pending': '#ffc107',
            'sent': '#28a745',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')

    @admin.action(description=_('Mark selected notifications as sent'))
    def mark_as_sent(self, request, queryset):
        """Bulk action to mark notifications as sent."""
        from django.utils import timezone
        updated = queryset.update(
            status=Notification.Status.SENT,
            sent_at=timezone.now()
        )
        self.message_user(
            request,
            _(f'{updated} notification(s) marked as sent.')
        )

    @admin.action(description=_('Mark selected notifications as failed'))
    def mark_as_failed(self, request, queryset):
        """Bulk action to mark notifications as failed."""
        updated = queryset.update(status=Notification.Status.FAILED)
        self.message_user(
            request,
            _(f'{updated} notification(s) marked as failed.')
        )

    @admin.action(description=_('Mark selected notifications as pending'))
    def mark_as_pending(self, request, queryset):
        """Bulk action to mark notifications as pending."""
        updated = queryset.update(
            status=Notification.Status.PENDING,
            sent_at=None
        )
        self.message_user(
            request,
            _(f'{updated} notification(s) marked as pending.')
        )
