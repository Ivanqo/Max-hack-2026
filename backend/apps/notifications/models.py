from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    """
    Notification model for sending messages to students.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        SIMULATED = 'simulated', _('Simulated')
        SENT = 'sent', _('Sent')
        FAILED = 'failed', _('Failed')

    class DeliveryStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        SIMULATED = 'simulated', _('Simulated')
        SENT = 'sent', _('Sent')
        FAILED = 'failed', _('Failed')

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Student'),
        help_text=_('The student who will receive this notification')
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        help_text=_('Notification title')
    )

    message = models.TextField(
        verbose_name=_('Message'),
        help_text=_('Notification message content')
    )

    opportunity = models.ForeignKey(
        'opportunities.Opportunity',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name=_('Opportunity'),
        help_text=_('Related opportunity (optional)')
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('Status'),
        help_text=_('Legacy delivery status kept for API compatibility')
    )

    delivery_status = models.CharField(
        max_length=10,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
        verbose_name=_('Delivery Status'),
        help_text=_('Provider delivery status')
    )

    provider = models.CharField(
        max_length=32,
        blank=True,
        verbose_name=_('Provider'),
        help_text=_('Notification provider used for delivery')
    )

    provider_message_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_('Provider Message ID'),
        help_text=_('External message identifier returned by MAX')
    )

    idempotency_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_('Idempotency Key'),
        help_text=_('Unique key preventing duplicate notifications')
    )

    last_error = models.TextField(
        blank=True,
        verbose_name=_('Last Error'),
        help_text=_('Sanitized last delivery error')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
        help_text=_('When the notification was created')
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Sent At'),
        help_text=_('When the notification was sent')
    )

    failed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Failed At'),
        help_text=_('When the last delivery attempt failed')
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Read At'),
        help_text=_('When the student marked this notification as read')
    )

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['student', 'delivery_status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['delivery_status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.student} ({self.get_status_display()})"

    def mark_as_sent(self, provider_message_id=None, provider='max'):
        """Mark notification as sent with current timestamp."""
        from django.utils import timezone
        self.status = self.Status.SENT
        self.delivery_status = self.DeliveryStatus.SENT
        self.provider = provider
        if provider_message_id:
            self.provider_message_id = provider_message_id
        self.sent_at = timezone.now()
        self.failed_at = None
        self.last_error = ''
        self.save(update_fields=[
            'status',
            'delivery_status',
            'provider',
            'provider_message_id',
            'sent_at',
            'failed_at',
            'last_error',
        ])

    def mark_as_simulated(self, provider_message_id=None):
        """Mark notification as delivered by the mock/dev adapter."""
        from django.utils import timezone
        self.status = self.Status.SIMULATED
        self.delivery_status = self.DeliveryStatus.SIMULATED
        self.provider = 'mock'
        if provider_message_id:
            self.provider_message_id = provider_message_id
        self.sent_at = timezone.now()
        self.failed_at = None
        self.last_error = ''
        self.save(update_fields=[
            'status',
            'delivery_status',
            'provider',
            'provider_message_id',
            'sent_at',
            'failed_at',
            'last_error',
        ])

    def mark_as_failed(self, error='Delivery failed'):
        """Mark notification as failed."""
        from django.utils import timezone
        self.status = self.Status.FAILED
        self.delivery_status = self.DeliveryStatus.FAILED
        self.failed_at = timezone.now()
        self.last_error = str(error)[:1000]
        self.save(update_fields=['status', 'delivery_status', 'failed_at', 'last_error'])

    def mark_as_read(self):
        """Mark notification as read without changing provider delivery state."""
        from django.utils import timezone
        self.read_at = timezone.now()
        self.save(update_fields=['read_at'])


class MaxWebhookEvent(models.Model):
    """Stores MAX webhook update ids to make webhook processing idempotent."""

    event_id = models.CharField(max_length=255, unique=True, db_index=True)
    event_type = models.CharField(max_length=100, blank=True)
    payload = models.JSONField(default=dict)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('MAX Webhook Event')
        verbose_name_plural = _('MAX Webhook Events')
        ordering = ['-processed_at']
        indexes = [
            models.Index(fields=['event_type', '-processed_at']),
        ]

    def __str__(self):
        return f'{self.event_type or "max_update"}:{self.event_id}'
