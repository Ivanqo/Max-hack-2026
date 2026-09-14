from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.knowledge.models import KnowledgeItem
from apps.opportunities.models import Opportunity
from apps.universities.models import University


class SeedDemoCommandTest(TestCase):
    def test_seed_demo_is_idempotent_and_creates_demo_scope(self):
        call_command('seed_demo', verbosity=0)
        call_command('seed_demo', verbosity=0)

        User = get_user_model()
        self.assertEqual(University.objects.count(), 2)
        self.assertTrue(User.objects.filter(email='student@demo.local').exists())
        self.assertGreaterEqual(KnowledgeItem.objects.filter(university='Demo University').count(), 20)
        self.assertGreaterEqual(Opportunity.objects.filter(university='Demo University').count(), 10)
        self.assertTrue(
            Opportunity.objects.filter(
                university='North Tech University',
                title='North-only Robotics Internship',
            ).exists()
        )
