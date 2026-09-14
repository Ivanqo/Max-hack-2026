from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.notifications.models import Notification
from apps.notifications.services import get_notification_service
from apps.opportunities.models import Opportunity
from apps.subscriptions.models import Subscription


class NotificationServiceTest(TestCase):
    def test_subscription_creates_simulated_notification_for_matching_opportunity(self):
        User = get_user_model()
        student = User.objects.create_user(
            email='notify@test.local',
            password='pass12345',
            role='student',
            university='Demo University',
        )
        Subscription.objects.create(student=student, topic='Backend', active=True)
        opportunity = Opportunity.objects.create(
            university='Demo University',
            type='internship',
            title='Backend Internship',
            description='Build APIs.',
            requirements='Python',
            verified_status='verified',
            published=True,
        )

        notifications = get_notification_service().create_for_opportunity_subscriptions(opportunity)

        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].status, Notification.Status.SIMULATED)
