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
        help_text=_('Current notification status')
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

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.student} ({self.get_status_display()})"

    def mark_as_sent(self):
        """Mark notification as sent with current timestamp."""
        from django.utils import timezone
        self.status = self.Status.SENT
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])

    def mark_as_simulated(self):
        """Mark notification as delivered by the mock/dev adapter."""
        from django.utils import timezone
        self.status = self.Status.SIMULATED
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])

    def mark_as_failed(self):
        """Mark notification as failed."""
        self.status = self.Status.FAILED
        self.save(update_fields=['status'])
