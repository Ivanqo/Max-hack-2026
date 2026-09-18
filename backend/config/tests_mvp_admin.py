"""Regression tests for the admin CRUD surface in config/mvp_views.py.

These cover the exact bug reported by the product review: admin edit forms
that accepted fields (CareerRole avg salary/education path, Opportunity
deadline/source/verified status/skills, Knowledge audience/verified
status/published/actual-until) which the backend silently dropped, so the
value reverted after reload. Every field asserted here must round-trip
through create -> reload and update -> reload.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.careers.models import CareerRole
from apps.knowledge.models import KnowledgeItem
from apps.opportunities.models import Opportunity

User = get_user_model()


def _admin_client():
    admin = User.objects.create_user(
        email='mvp-admin@test.local',
        password='pass12345',
        role='admin',
        university='Demo University',
        is_staff=True,
    )
    client = APIClient()
    client.force_authenticate(user=admin)
    return client, admin


class AdminCareerRoleFieldsTest(TestCase):
    def test_avg_salary_demand_level_and_education_path_persist(self):
        client, _ = _admin_client()

        create = client.post(
            '/api/admin/career-roles',
            {
                'title': 'Backend Developer',
                'description': 'Build APIs.',
                'avgSalary': '150 000 - 220 000 ₽',
                'demandLevel': 'medium',
                'educationPath': ['Learn Python', 'Ship a project', 'Apply to internships'],
                'skills': [{'name': 'Python', 'level': 4}],
            },
            format='json',
        )
        self.assertEqual(create.status_code, 201)
        self.assertEqual(create.data['avgSalary'], '150 000 - 220 000 ₽')
        self.assertEqual(create.data['demandLevel'], 'medium')
        self.assertEqual(
            create.data['educationPath'],
            ['Learn Python', 'Ship a project', 'Apply to internships'],
        )

        role = CareerRole.objects.get(pk=create.data['id'])
        self.assertEqual(role.avg_salary, '150 000 - 220 000 ₽')
        self.assertEqual(role.demand_level, 'medium')

        update = client.put(
            f"/api/admin/career-roles/{role.id}",
            {
                'title': 'Backend Developer',
                'description': 'Build APIs.',
                'avgSalary': '180 000 - 260 000 ₽',
                'demandLevel': 'high',
                'educationPath': ['Learn Django'],
            },
            format='json',
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.data['avgSalary'], '180 000 - 260 000 ₽')
        self.assertEqual(update.data['demandLevel'], 'high')
        self.assertEqual(update.data['educationPath'], ['Learn Django'])

        role.refresh_from_db()
        self.assertEqual(role.avg_salary, '180 000 - 260 000 ₽')
        self.assertEqual(role.demand_level, 'high')
        self.assertEqual(role.education_path, ['Learn Django'])


class AdminOpportunityFieldsTest(TestCase):
    def test_deadline_source_verified_status_and_skills_persist(self):
        client, _ = _admin_client()

        create = client.post(
            '/api/admin/opportunities',
            {
                'title': 'Backend Internship',
                'description': 'Build APIs.',
                'type': 'internship',
                'company': 'MAX Labs',
                'location': 'Campus',
                'remote': True,
                'requirements': ['Python'],
                'deadline': '2030-01-15T00:00:00Z',
                'sourceUrl': 'https://example.org/jobs/1',
                'verifiedStatus': 'pending',
                'published': True,
                'skills': [{'name': 'Python', 'level': 4}],
            },
            format='json',
        )
        self.assertEqual(create.status_code, 201)
        self.assertEqual(create.data['verifiedStatus'], 'pending')
        self.assertEqual(create.data['sourceUrl'], 'https://example.org/jobs/1')
        self.assertTrue(create.data['deadline'].startswith('2030-01-15'))
        self.assertEqual(create.data['skills'], [{'name': 'Python', 'level': 4, 'weight': 1}])

        item = Opportunity.objects.get(pk=create.data['id'])
        self.assertEqual(item.verified_status, 'pending')
        self.assertEqual(item.source_url, 'https://example.org/jobs/1')
        self.assertEqual(item.required_skills.count(), 1)

        update = client.put(
            f"/api/admin/opportunities/{item.id}",
            {
                'title': 'Backend Internship',
                'description': 'Build APIs.',
                'type': 'internship',
                'requirements': ['Python'],
                'sourceUrl': 'https://example.org/jobs/1',
                'verifiedStatus': 'verified',
                'published': True,
            },
            format='json',
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.data['verifiedStatus'], 'verified')

        item.refresh_from_db()
        self.assertEqual(item.verified_status, 'verified')
        self.assertTrue(item.published)

    def test_legacy_status_field_still_publishes_for_contest_contract(self):
        """DATA-API.yaml calls this endpoint with `status: active` and no
        `published`/`verifiedStatus` field and expects an immediately live,
        verified, notification-triggering opportunity."""
        client, _ = _admin_client()

        create = client.post(
            '/api/admin/opportunities',
            {
                'title': 'Legacy Contract Internship',
                'description': 'Build APIs.',
                'type': 'internship',
                'company': 'MAX Labs',
                'location': 'Campus',
                'remote': True,
                'requirements': ['Python', 'Django', 'REST'],
                'status': 'active',
            },
            format='json',
        )
        self.assertEqual(create.status_code, 201)
        item = Opportunity.objects.get(pk=create.data['id'])
        self.assertTrue(item.published)
        self.assertEqual(item.verified_status, 'verified')


class AdminKnowledgeFieldsTest(TestCase):
    def test_audience_verified_status_published_and_actual_until_persist(self):
        client, _ = _admin_client()

        create = client.post(
            '/api/admin/knowledge',
            {
                'title': 'How to apply for practice',
                'content': 'Visit the career office...',
                'category': 'Career Center',
                'sourceUrl': 'https://example.org/practice',
                'audience': ['students', 'freshmen'],
                'verifiedStatus': 'draft',
                'published': False,
                'actualUntil': '2030-06-01',
            },
            format='json',
        )
        self.assertEqual(create.status_code, 201)
        self.assertEqual(create.data['verifiedStatus'], 'draft')
        self.assertFalse(create.data['published'])
        self.assertEqual(create.data['audience'], ['students', 'freshmen'])
        self.assertEqual(create.data['actualUntil'], '2030-06-01')

        item = KnowledgeItem.objects.get(pk=create.data['id'])
        self.assertEqual(item.verified_status, 'draft')
        self.assertFalse(item.published)
        self.assertEqual(item.audience, ['students', 'freshmen'])

        update = client.put(
            f"/api/admin/knowledge/{item.id}",
            {
                'title': 'How to apply for practice',
                'content': 'Visit the career office...',
                'category': 'Career Center',
                'verifiedStatus': 'verified',
                'published': True,
                'actualUntil': '2031-01-01',
            },
            format='json',
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.data['verifiedStatus'], 'verified')
        self.assertTrue(update.data['published'])
        self.assertEqual(update.data['actualUntil'], '2031-01-01')

        item.refresh_from_db()
        self.assertEqual(item.verified_status, 'verified')
        self.assertTrue(item.published)
        self.assertEqual(str(item.actual_until), '2031-01-01')
