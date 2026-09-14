from django.db import models
from django.conf import settings
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex


class KnowledgeItemManager(models.Manager):
    """Custom manager for KnowledgeItem with full-text search capabilities."""

    def search(self, query):
        """Perform full-text search on title and content."""
        from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

        search_vector = SearchVector('title', weight='A') + SearchVector('content', weight='B')
        search_query = SearchQuery(query)

        return self.filter(published=True).annotate(
            rank=SearchRank(search_vector, search_query)
        ).filter(rank__gte=0.01).order_by('-rank')

    def published(self):
        """Return only published knowledge items."""
        return self.filter(published=True)

    def verified(self):
        """Return only verified knowledge items."""
        return self.filter(verified_status='verified', published=True)

    def by_university(self, university_name):
        """Filter by university."""
        return self.filter(university__iexact=university_name)

    def for_audience(self, audience_type):
        """Filter items that target specific audience."""
        return self.filter(audience__contains=[audience_type])


class KnowledgeItem(models.Model):
    """Knowledge base items with verification and targeting capabilities."""

    VERIFIED_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('verified', 'Verified'),
        ('outdated', 'Outdated'),
    ]

    AUDIENCE_CHOICES = [
        'all',
        'students',
        'freshmen',
        'graduates',
        'postgraduates',
        'international',
        'local',
    ]

    university = models.CharField(
        max_length=255,
        db_index=True,
        help_text='University this knowledge item belongs to'
    )
    title = models.CharField(
        max_length=500,
        help_text='Title of the knowledge item'
    )
    content = models.TextField(
        help_text='Main content of the knowledge item (supports markdown)'
    )
    source_url = models.URLField(
        max_length=1000,
        blank=True,
        help_text='Original source URL if applicable'
    )
    responsible_unit = models.CharField(
        max_length=255,
        blank=True,
        help_text='Department or unit responsible for this information'
    )
    audience = models.JSONField(
        default=list,
        blank=True,
        help_text='Target audience for this knowledge item'
    )
    verified_status = models.CharField(
        max_length=20,
        choices=VERIFIED_STATUS_CHOICES,
        default='draft',
        db_index=True,
        help_text='Verification status of the content'
    )
    published = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Whether this item is visible to users'
    )
    actual_until = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text='Date until which this information is valid'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_knowledge_items',
        help_text='User who created this knowledge item'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    search_vector = SearchVectorField(null=True, blank=True)

    objects = KnowledgeItemManager()

    class Meta:
        verbose_name = 'Knowledge Item'
        verbose_name_plural = 'Knowledge Items'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['university', 'published']),
            models.Index(fields=['university', 'verified_status']),
            models.Index(fields=['verified_status', 'published']),
            models.Index(fields=['actual_until']),
            models.Index(fields=['-created_at']),
            GinIndex(fields=['search_vector'], name='knowledge_search_idx'),
        ]

    def __str__(self):
        return f"{self.title} ({self.university})"

    def is_current(self):
        """Check if the knowledge item is still current."""
        if not self.actual_until:
            return True
        from django.utils import timezone
        return self.actual_until >= timezone.now().date()

    def mark_outdated(self):
        """Mark the knowledge item as outdated."""
        self.verified_status = 'outdated'
        self.save(update_fields=['verified_status', 'updated_at'])

    def verify(self):
        """Mark the knowledge item as verified."""
        self.verified_status = 'verified'
        self.save(update_fields=['verified_status', 'updated_at'])

    def publish(self):
        """Publish the knowledge item."""
        self.published = True
        self.save(update_fields=['published', 'updated_at'])

    def unpublish(self):
        """Unpublish the knowledge item."""
        self.published = False
        self.save(update_fields=['published', 'updated_at'])


class KnowledgeReport(models.Model):
    """Reports submitted by users about knowledge items."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewing', 'Under Review'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    ]

    university = models.CharField(
        max_length=255,
        db_index=True,
        help_text='University context for this report'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='knowledge_reports',
        help_text='User who submitted the report'
    )
    knowledge_item = models.ForeignKey(
        KnowledgeItem,
        on_delete=models.CASCADE,
        related_name='reports',
        help_text='Knowledge item being reported'
    )
    reason = models.TextField(
        help_text='Reason for the report'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text='Current status of the report'
    )
    resolution_note = models.TextField(
        blank=True,
        help_text='Admin note about how the report was resolved'
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_knowledge_reports',
        help_text='Admin who resolved the report'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the report was resolved'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Knowledge Report'
        verbose_name_plural = 'Knowledge Reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['university', 'status']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['knowledge_item', 'status']),
            models.Index(fields=['-created_at']),
        ]
        unique_together = [['student', 'knowledge_item']]

    def __str__(self):
        return f"Report by {self.student.email} on '{self.knowledge_item.title}'"

    def resolve(self, resolved_by, resolution_note=''):
        """Mark report as resolved."""
        from django.utils import timezone
        self.status = 'resolved'
        self.resolved_by = resolved_by
        self.resolved_at = timezone.now()
        self.resolution_note = resolution_note
        self.save(update_fields=['status', 'resolved_by', 'resolved_at', 'resolution_note', 'updated_at'])

    def reject(self, resolved_by, resolution_note=''):
        """Mark report as rejected."""
        from django.utils import timezone
        self.status = 'rejected'
        self.resolved_by = resolved_by
        self.resolved_at = timezone.now()
        self.resolution_note = resolution_note
        self.save(update_fields=['status', 'resolved_by', 'resolved_at', 'resolution_note', 'updated_at'])

    def start_review(self):
        """Mark report as under review."""
        self.status = 'reviewing'
        self.save(update_fields=['status', 'updated_at'])
