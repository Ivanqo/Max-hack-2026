from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Subscription(models.Model):
    """
    Student subscription to job postings with topic and filter criteria.
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        help_text='Student who owns this subscription'
    )
    topic = models.CharField(
        max_length=255,
        help_text='Topic or category for the subscription'
    )
    filters = models.JSONField(
        default=dict,
        blank=True,
        help_text='JSON object containing filter criteria (e.g., location, salary, experience level)'
    )
    active = models.BooleanField(
        default=True,
        help_text='Whether this subscription is active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'active']),
            models.Index(fields=['topic']),
        ]
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'

    def __str__(self):
        status = 'Active' if self.active else 'Inactive'
        name = self.student.username or self.student.email
        return f"{name} - {self.topic} ({status})"
