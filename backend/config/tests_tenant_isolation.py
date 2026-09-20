"""Regression tests for tenant isolation in the demo admin surface.

The seeded `role='admin'` users are university-scoped admins. They must not
see another Moscow university's opportunities, knowledge items, career roles,
or user accounts through the admin panel's list endpoints.
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
        self.assertNotIn('Стажировка инженера БПЛА в лаборатории МАИ', titles)
        self.assertTrue(all('МАИ' not in u for u in universities))

    def test_demo_admin_cannot_see_north_tenant_knowledge(self):
        client = self._login('admin@demo.local')
        response = client.get('/api/admin/knowledge')
        self.assertEqual(response.status_code, 200)
        titles = [item['title'] for item in response.data]
        self.assertFalse(any('Правила проектной практики МАИ' in t for t in titles))

    def test_demo_admin_cannot_see_north_tenant_career_roles(self):
        client = self._login('admin@demo.local')
        response = client.get('/api/admin/career-roles')
        self.assertEqual(response.status_code, 200)
        titles = [item['title'] for item in response.data]
        self.assertFalse(any('БПЛА' in t or 'авионике' in t for t in titles))

    def test_demo_admin_cannot_see_mai_tenant_users(self):
        client = self._login('admin@demo.local')
        response = client.get('/api/v1/accounts/users/')
        self.assertEqual(response.status_code, 200)
        emails = {item['email'] for item in response.data['results']}
        universities = {item['university'] for item in response.data['results']}
        self.assertNotIn('student@north.local', emails)
        self.assertEqual(universities, {'НИУ МГСУ'})

    def test_north_admin_only_sees_its_own_tenant(self):
        client = self._login('admin@north.local')
        response = client.get('/api/admin/opportunities')
        self.assertEqual(response.status_code, 200)
        titles = {item['title'] for item in response.data}
        self.assertIn('Стажировка инженера БПЛА в лаборатории МАИ', titles)
        self.assertNotIn('Стажировка BIM-моделировщика в Мосинжпроекте', titles)
