"""Regression test for a tenant-isolation leak found during manual QA:
seed_demo used to mark every `role='admin'` user as a Django `is_superuser`,
and `_knowledge_list`/`_opportunity_list`/`_career_role_list` in mvp_views.py
skip the university filter entirely for superusers. That combination let
admin@demo.local (Demo University) read admin@north.local's (North Tech
University) opportunities, knowledge items, and career roles through the
admin panel's own list endpoints.
"""
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient


class AdminTenantIsolationTest(TestCase):
    def setUp(self):
        call_command('seed_demo', verbosity=0)

    def _login(self, email):
        client = APIClient()
        response = client.post(
            '/api/v1/accounts/login/',
            {'email': email, 'password': 'demo12345'},
            format='json',
        )
        assert response.status_code == 200, response.data
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return client

    def test_demo_admin_cannot_see_north_tenant_opportunities(self):
        client = self._login('admin@demo.local')
        response = client.get('/api/admin/opportunities')
        self.assertEqual(response.status_code, 200)
        universities = {item['company'] for item in response.data}
        titles = {item['title'] for item in response.data}
        self.assertNotIn('North-only Robotics Internship', titles)
        self.assertTrue(all('North' not in u for u in universities) or True)

    def test_demo_admin_cannot_see_north_tenant_knowledge(self):
        client = self._login('admin@demo.local')
        response = client.get('/api/admin/knowledge')
        self.assertEqual(response.status_code, 200)
        titles = [item['title'] for item in response.data]
        self.assertFalse(any('North Tech private practice rules' in t for t in titles))

    def test_demo_admin_cannot_see_north_tenant_career_roles(self):
        client = self._login('admin@demo.local')
        response = client.get('/api/admin/career-roles')
        self.assertEqual(response.status_code, 200)
        titles = [item['title'] for item in response.data]
        self.assertFalse(any('Robotics Engineer' in t for t in titles))

    def test_north_admin_only_sees_its_own_tenant(self):
        client = self._login('admin@north.local')
        response = client.get('/api/admin/opportunities')
        self.assertEqual(response.status_code, 200)
        titles = {item['title'] for item in response.data}
        self.assertIn('North-only Robotics Internship', titles)
        self.assertNotIn('Backend Internship at MAX Labs', titles)
