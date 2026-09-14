from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import KnowledgeItem, KnowledgeReport


@admin.register(KnowledgeItem)
class KnowledgeItemAdmin(admin.ModelAdmin):
    """Admin interface for KnowledgeItem model."""

    list_display = [
        'title',
        'university',
        'verified_status_badge',
        'published_badge',
        'responsible_unit',
        'actual_until',
        'created_by',
        'created_at',
    ]
    list_filter = [
        'verified_status',
        'published',
        'university',
        'created_at',
        'actual_until',
    ]
    search_fields = [
        'title',
        'content',
        'university',
        'responsible_unit',
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'created_by',
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'university',
                'title',
                'content',
                'source_url',
                'responsible_unit',
            )
        }),
        ('Targeting & Status', {
            'fields': (
                'audience',
                'verified_status',
                'published',
                'actual_until',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'created_at'
    actions = [
        'mark_as_verified',
        'mark_as_outdated',
        'publish_items',
        'unpublish_items',
    ]
    list_per_page = 50

    def verified_status_badge(self, obj):
        """Display colored badge for verification status."""
        colors = {
            'draft': 'gray',
            'verified': 'green',
            'outdated': 'red',
        }
        color = colors.get(obj.verified_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_verified_status_display()
        )
    verified_status_badge.short_description = 'Status'

    def published_badge(self, obj):
        """Display colored badge for published status."""
        if obj.published:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">Published</span>'
            )
        return format_html(
            '<span style="background-color: gray; color: white; padding: 3px 10px; border-radius: 3px;">Draft</span>'
        )
    published_badge.short_description = 'Published'

    def mark_as_verified(self, request, queryset):
        """Mark selected items as verified."""
        updated = queryset.update(verified_status='verified', updated_at=timezone.now())
        self.message_user(request, f'{updated} knowledge items marked as verified.')
    mark_as_verified.short_description = 'Mark selected items as verified'

    def mark_as_outdated(self, request, queryset):
        """Mark selected items as outdated."""
        updated = queryset.update(verified_status='outdated', updated_at=timezone.now())
        self.message_user(request, f'{updated} knowledge items marked as outdated.')
    mark_as_outdated.short_description = 'Mark selected items as outdated'

    def publish_items(self, request, queryset):
        """Publish selected items."""
        updated = queryset.update(published=True, updated_at=timezone.now())
        self.message_user(request, f'{updated} knowledge items published.')
    publish_items.short_description = 'Publish selected items'

    def unpublish_items(self, request, queryset):
        """Unpublish selected items."""
        updated = queryset.update(published=False, updated_at=timezone.now())
        self.message_user(request, f'{updated} knowledge items unpublished.')
    unpublish_items.short_description = 'Unpublish selected items'

    def save_model(self, request, obj, form, change):
        """Set created_by to current user if not set."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(KnowledgeReport)
class KnowledgeReportAdmin(admin.ModelAdmin):
    """Admin interface for KnowledgeReport model."""

    list_display = [
        'id',
        'student',
        'knowledge_item_link',
        'status_badge',
        'university',
        'created_at',
        'resolved_by',
    ]
    list_filter = [
        'status',
        'university',
        'created_at',
        'resolved_at',
    ]
    search_fields = [
        'student__email',
        'knowledge_item__title',
        'reason',
        'resolution_note',
    ]
    readonly_fields = [
        'student',
        'knowledge_item',
        'university',
        'created_at',
        'updated_at',
        'resolved_at',
    ]
    fieldsets = (
        ('Report Information', {
            'fields': (
                'student',
                'knowledge_item',
                'university',
                'reason',
                'status',
            )
        }),
        ('Resolution', {
            'fields': (
                'resolution_note',
                'resolved_by',
                'resolved_at',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'created_at'
    actions = [
        'start_review',
        'mark_as_resolved',
        'mark_as_rejected',
    ]
    list_per_page = 50

    def knowledge_item_link(self, obj):
        """Display link to knowledge item."""
        url = reverse('admin:knowledge_knowledgeitem_change', args=[obj.knowledge_item.id])
        return format_html('<a href="{}">{}</a>', url, obj.knowledge_item.title)
    knowledge_item_link.short_description = 'Knowledge Item'

    def status_badge(self, obj):
        """Display colored badge for status."""
        colors = {
            'pending': 'orange',
            'reviewing': 'blue',
            'resolved': 'green',
            'rejected': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def start_review(self, request, queryset):
        """Mark selected reports as under review."""
        updated = queryset.filter(status='pending').update(
            status='reviewing',
            updated_at=timezone.now()
        )
        self.message_user(request, f'{updated} reports marked as under review.')
    start_review.short_description = 'Start review for selected reports'

    def mark_as_resolved(self, request, queryset):
        """Mark selected reports as resolved."""
        updated = 0
        for report in queryset:
            if report.status != 'resolved':
                report.resolve(request.user, 'Bulk resolved by admin')
                updated += 1
        self.message_user(request, f'{updated} reports marked as resolved.')
    mark_as_resolved.short_description = 'Mark selected reports as resolved'

    def mark_as_rejected(self, request, queryset):
        """Mark selected reports as rejected."""
        updated = 0
        for report in queryset:
            if report.status != 'rejected':
                report.reject(request.user, 'Bulk rejected by admin')
                updated += 1
        self.message_user(request, f'{updated} reports marked as rejected.')
    mark_as_rejected.short_description = 'Mark selected reports as rejected'
