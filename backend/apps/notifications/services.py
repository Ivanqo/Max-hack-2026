"""
Notification Service - Handles notification creation and delivery.
"""
import logging
from typing import Optional, Dict, Any
from django.conf import settings
from django.utils import timezone
from apps.notifications.integrations.max.observability import log_max_event, new_correlation_id
from .models import Notification
from apps.subscriptions.models import Subscription
from .integrations.max import MaxClient, MockMaxClient, RealMaxClient

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for managing notifications with adapter pattern for MAX API integration.
    Gracefully handles MAX API unavailability.
    """

    def __init__(self, client: Optional[MaxClient] = None):
        """
        Initialize notification service.

        Args:
            client: Optional MAX client instance. If not provided, will be created
                   based on USE_MOCK_MAX_CLIENT setting (defaults to MockMaxClient).
        """
        if client:
            self._client = client
        else:
            use_mock = getattr(settings, 'USE_MOCK_MAX_CLIENT', True)
            if use_mock:
                self._client = MockMaxClient()
                logger.info("NotificationService using MockMaxClient")
            else:
                self._client = RealMaxClient()
                logger.info("NotificationService using RealMaxClient")

    def create_notification(
        self,
        student,
        title: str,
        message: str,
        opportunity=None,
        idempotency_key: str | None = None,
    ) -> Notification:
        """
        Create a new notification in the database.

        Args:
            student: Student model instance
            title: Notification title
            message: Notification message content
            opportunity: Optional Opportunity model instance

        Returns:
            Created Notification instance
        """
        defaults = {
            'student': student,
            'title': title,
            'message': message,
            'opportunity': opportunity,
            'status': Notification.Status.PENDING,
            'delivery_status': Notification.DeliveryStatus.PENDING,
        }
        if idempotency_key:
            notification, created = Notification.objects.get_or_create(
                idempotency_key=idempotency_key,
                defaults=defaults,
            )
            if not created:
                logger.info("Notification already exists for the requested idempotency key")
                return notification
        else:
            notification = Notification.objects.create(**defaults)

        logger.info("Notification created")

        return notification

    def send(self, notification: Notification) -> bool:
        """
        Send a notification using the configured MAX client.
        Gracefully handles MAX API unavailability.

        Args:
            notification: Notification instance to send

        Returns:
            bool: True if successfully sent, False otherwise
        """
        correlation_id = new_correlation_id()
        if notification.delivery_status in [
            Notification.DeliveryStatus.SENT,
            Notification.DeliveryStatus.SIMULATED,
        ]:
            log_max_event(
                logger,
                'max_notification_delivery',
                correlation_id,
                provider=notification.provider or 'max',
                result='already_delivered',
                stage='delivery',
            )
            return True

        # Check if MAX API is available
        if not self._client.is_available():
            log_max_event(
                logger,
                'max_notification_delivery',
                correlation_id,
                provider='max',
                result='unavailable',
                stage='delivery',
            )
            return False

        # Prepare metadata
        metadata = {
            'notification_id': str(notification.id),
            'created_at': notification.created_at.isoformat(),
            'max_user_id': notification.student.max_user_id,
            'webapp_payload': (
                f'opportunity_{notification.opportunity.id}'
                if notification.opportunity else 'notifications'
            ),
            'correlation_id': correlation_id,
        }

        try:
            # Send through MAX client
            result = self._client.send_notification(
                student_id=str(notification.student.id),
                title=notification.title,
                message=notification.message,
                opportunity_id=str(notification.opportunity.id) if notification.opportunity else None,
                metadata=metadata
            )

            mode_is_mock = bool(getattr(settings, 'USE_MOCK_MAX_CLIENT', True))
            returned_provider = result.get('provider') if isinstance(result, dict) else None
            provider = 'mock' if mode_is_mock or returned_provider == 'mock' else (
                'max' if returned_provider == 'max' else 'unknown'
            )
            delivered = bool(isinstance(result, dict) and result.get('success'))
            if not mode_is_mock and provider != 'max':
                delivered = False

            if delivered:
                if provider == 'mock':
                    notification.mark_as_simulated(
                        provider_message_id=result.get('message_id')
                    )
                else:
                    notification.mark_as_sent(
                        provider_message_id=result.get('message_id'),
                        provider=result.get('provider', 'max'),
                    )

                log_max_event(
                    logger,
                    'max_notification_delivery',
                    correlation_id,
                    provider=provider,
                    result='simulated' if provider == 'mock' else 'sent',
                    stage='delivery',
                )
                return True
            else:
                # Mark as failed
                notification.mark_as_failed(result.get('error') or 'Delivery failed')

                log_max_event(
                    logger,
                    'max_notification_delivery',
                    correlation_id,
                    provider=provider,
                    result='failed',
                    stage='delivery',
                )
                return False

        except Exception:
            # Handle unexpected errors gracefully
            notification.mark_as_failed('Unexpected delivery error')

            log_max_event(
                logger,
                'max_notification_delivery',
                correlation_id,
                provider='max',
                result='failed',
                stage='delivery',
            )
            return False

    def send_notification(
        self,
        student,
        title: str,
        message: str,
        opportunity=None,
        idempotency_key: str | None = None,
    ) -> tuple[Notification, bool]:
        """
        Create and send a notification in one operation.

        Args:
            student: Student model instance
            title: Notification title
            message: Notification message content
            opportunity: Optional Opportunity model instance

        Returns:
            Tuple of (Notification instance, bool indicating if sent successfully)
        """
        notification = self.create_notification(
            student=student,
            title=title,
            message=message,
            opportunity=opportunity,
            idempotency_key=idempotency_key,
        )

        success = (
            True
            if notification.delivery_status in [
                Notification.DeliveryStatus.SENT,
                Notification.DeliveryStatus.SIMULATED,
            ]
            else self.send(notification)
        )

        return notification, success

    def create_for_opportunity_subscriptions(self, opportunity) -> list[Notification]:
        """Create notifications for active subscriptions matching an opportunity."""
        text = self._opportunity_text(opportunity)
        subscriptions = Subscription.objects.filter(
            active=True,
            student__role='student',
            student__university=opportunity.university,
        ).select_related('student')

        notifications = []
        for subscription in subscriptions:
            if not self._subscription_matches(subscription, opportunity, text):
                continue

            title = f'Новая возможность: {opportunity.title}'
            idempotency_key = f'subscription:{subscription.id}:opportunity:{opportunity.id}'
            notification = self.create_notification(
                student=subscription.student,
                title=title,
                message=f'Появилась релевантная opportunity по подписке "{subscription.topic}".',
                opportunity=opportunity,
                idempotency_key=idempotency_key,
            )
            if notification.delivery_status == Notification.DeliveryStatus.PENDING:
                self.send(notification)
            notifications.append(notification)

        return notifications

    def _subscription_matches(self, subscription: Subscription, opportunity, text: str) -> bool:
        topic = subscription.topic.lower().strip()
        if not topic:
            return False
        if topic in text or topic == opportunity.type:
            return True
        filters = subscription.filters or {}
        for value in filters.values():
            if isinstance(value, list) and any(str(item).lower() in text for item in value):
                return True
            if isinstance(value, str) and value.lower() in text:
                return True
        return False

    def _opportunity_text(self, opportunity) -> str:
        audience = ' '.join(str(value) for value in (opportunity.audience or {}).values())
        return f'{opportunity.title} {opportunity.description} {opportunity.requirements} {opportunity.type} {audience}'.lower()

    def retry_failed_notifications(self, limit: int = 100) -> Dict[str, Any]:
        """
        Retry sending failed notifications.

        Args:
            limit: Maximum number of notifications to retry

        Returns:
            Dict with retry statistics
        """
        failed_notifications = Notification.objects.filter(
            status=Notification.Status.FAILED
        ).order_by('created_at')[:limit]

        results = {
            'total': 0,
            'succeeded': 0,
            'failed': 0
        }

        for notification in failed_notifications:
            results['total'] += 1

            # Reset to pending before retry
            notification.status = Notification.Status.PENDING
            notification.delivery_status = Notification.DeliveryStatus.PENDING
            notification.failed_at = None
            notification.last_error = ''
            notification.save(update_fields=[
                'status',
                'delivery_status',
                'failed_at',
                'last_error',
            ])

            if self.send(notification):
                results['succeeded'] += 1
            else:
                results['failed'] += 1

        logger.info(
            f"Retry completed - Total: {results['total']}, "
            f"Succeeded: {results['succeeded']}, Failed: {results['failed']}"
        )

        return results

    def get_client(self) -> MaxClient:
        """
        Get the current MAX client instance.

        Returns:
            MaxClient instance
        """
        return self._client

    def set_client(self, client: MaxClient):
        """
        Set a new MAX client instance (useful for testing).

        Args:
            client: MaxClient instance
        """
        self._client = client
        logger.info(f"MAX client changed to {client.__class__.__name__}")


# Convenience function to get default service instance
def get_notification_service() -> NotificationService:
    """
    Get the default NotificationService instance.

    Returns:
        NotificationService instance
    """
    return NotificationService()
