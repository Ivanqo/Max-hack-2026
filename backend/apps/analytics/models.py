from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class InteractionEvent(models.Model):
    """
    Tracks user interactions and events for analytics purposes.
    Records actions like viewing opportunities, saving items, searching, etc.
    """

    EVENT_TYPES = [
        ('view', 'View'),
        ('click', 'Click'),
        ('search', 'Search'),
        ('save', 'Save'),
        ('unsave', 'Unsave'),
        ('apply', 'Apply'),
        ('share', 'Share'),
        ('filter', 'Filter'),
        ('sort', 'Sort'),
        ('export', 'Export'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('signup', 'Signup'),
        ('knowledge_search', 'Knowledge Search'),
        ('knowledge_open', 'Knowledge Open'),
        ('knowledge_no_answer', 'Knowledge No Answer'),
        ('opportunity_open', 'Opportunity Open'),
        ('opportunity_save', 'Opportunity Save'),
        ('career_gps_open', 'Открытие карьерного навигатора'),
        ('subscription_created', 'Subscription Created'),
    ]

    ENTITY_TYPES = [
        ('opportunity', 'Opportunity'),
        ('user', 'User'),
        ('skill', 'Skill'),
        ('match', 'Match'),
        ('profile', 'Profile'),
        ('dashboard', 'Dashboard'),
        ('page', 'Page'),
        ('knowledge', 'Knowledge'),
        ('subscription', 'Subscription'),
        ('notification', 'Notification'),
    ]

    university = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interaction_events',
        help_text="User who performed the action (nullable for anonymous events)"
    )
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES,
        db_index=True,
        help_text="Type of interaction event"
    )
    entity_type = models.CharField(
        max_length=50,
        choices=ENTITY_TYPES,
        null=True,
        blank=True,
        help_text="Type of entity involved in the event"
    )
    entity_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="ID of the entity involved (if applicable)"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional event data (search terms, filters, etc.)"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Interaction Event'
        verbose_name_plural = 'Interaction Events'
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['university', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['university', 'event_type', '-created_at']),
        ]

    def __str__(self):
        user_info = self.user.email if self.user else 'Anonymous'
        entity_info = f"{self.entity_type}:{self.entity_id}" if self.entity_type else "N/A"
        return f"{user_info} - {self.event_type} - {entity_info} @ {self.created_at}"


class AuditLog(models.Model):
    """
    Tracks administrative actions for security and compliance.
    Records CRUD operations performed by admins/organizers.
    """

    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('verify', 'Verify'),
        ('reject', 'Reject'),
        ('publish', 'Publish'),
        ('unpublish', 'Unpublish'),
        ('approve', 'Approve'),
        ('ban', 'Ban'),
        ('unban', 'Unban'),
        ('assign', 'Assign'),
        ('unassign', 'Unassign'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('restore', 'Restore'),
    ]

    ENTITY_TYPES = [
        ('opportunity', 'Opportunity'),
        ('user', 'User'),
        ('skill', 'Skill'),
        ('match', 'Match'),
        ('profile', 'Profile'),
        ('settings', 'Settings'),
        ('report', 'Report'),
        ('knowledge', 'Knowledge'),
        ('career_role', 'Career Role'),
        ('notification', 'Notification'),
    ]

    university = models.CharField(max_length=255, db_index=True)
    admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        help_text="Admin/organizer who performed the action"
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_TYPES,
        db_index=True,
        help_text="Type of administrative action"
    )
    entity_type = models.CharField(
        max_length=50,
        choices=ENTITY_TYPES,
        help_text="Type of entity affected"
    )
    entity_id = models.CharField(
        max_length=255,
        help_text="ID of the affected entity"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional details (old/new values, reason, etc.)"
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp', '-id']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['university', '-timestamp']),
            models.Index(fields=['admin', '-timestamp']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['university', 'action', '-timestamp']),
        ]

    def __str__(self):
        admin_info = self.admin.email if self.admin else 'System'
        return f"{admin_info} - {self.action} {self.entity_type}:{self.entity_id} @ {self.timestamp}"
