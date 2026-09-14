from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Subscription

User = get_user_model()


class SubscriptionModelTest(TestCase):
    """
    Test cases for the Subscription model.
    """

    def setUp(self):
        """
        Create test user and subscription.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.subscription = Subscription.objects.create(
            student=self.user,
            topic='Python Developer',
            filters={'location': 'Remote', 'experience': 'Mid-level'},
            active=True
        )

    def test_subscription_creation(self):
        """
        Test that subscription is created correctly.
        """
        self.assertEqual(self.subscription.student, self.user)
        self.assertEqual(self.subscription.topic, 'Python Developer')
        self.assertTrue(self.subscription.active)
        self.assertIsInstance(self.subscription.filters, dict)

    def test_subscription_str_representation(self):
        """
        Test string representation of subscription.
        """
        expected = f"{self.user.username} - Python Developer (Active)"
        self.assertEqual(str(self.subscription), expected)

    def test_subscription_inactive_str(self):
        """
        Test string representation when subscription is inactive.
        """
        self.subscription.active = False
        self.subscription.save()
        expected = f"{self.user.username} - Python Developer (Inactive)"
        self.assertEqual(str(self.subscription), expected)

    def test_subscription_default_filters(self):
        """
        Test that filters default to empty dict.
        """
        sub = Subscription.objects.create(
            student=self.user,
            topic='Data Scientist'
        )
        self.assertEqual(sub.filters, {})

    def test_subscription_cascade_delete(self):
        """
        Test that subscriptions are deleted when user is deleted.
        """
        user_id = self.user.id
        self.user.delete()
        self.assertFalse(
            Subscription.objects.filter(student_id=user_id).exists()
        )
