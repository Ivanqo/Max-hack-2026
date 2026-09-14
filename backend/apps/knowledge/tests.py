from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.analytics.models import InteractionEvent
from apps.knowledge.models import KnowledgeItem
from apps.knowledge.services import KnowledgeSearchService


class KnowledgeSearchServiceTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.student = User.objects.create_user(
            email='student@test.local',
            password='pass12345',
            role='student',
            university='Demo University',
        )
        self.other_student = User.objects.create_user(
            email='other@test.local',
            password='pass12345',
            role='student',
            university='Other University',
        )
        self.item = KnowledgeItem.objects.create(
            university='Demo University',
            title='Как оформить производственную практику',
            content='Подайте заявление и загрузите договор практики.',
            source_url='https://demo.local/practice',
            responsible_unit='Учебный офис',
            audience=['students', 'практика'],
            verified_status='verified',
            published=True,
        )
        KnowledgeItem.objects.create(
            university='Other University',
            title='Как оформить производственную практику',
            content='Other tenant answer.',
            verified_status='verified',
            published=True,
        )

    def test_verified_search_returns_source_and_status(self):
        result = KnowledgeSearchService().search('производственную практику', self.student)

        self.assertTrue(result['found'])
        self.assertEqual(result['answer']['source_url'], self.item.source_url)
        self.assertEqual(result['answer']['verified_status'], 'verified')
        self.assertEqual(result['answer']['responsible_unit'], 'Учебный офис')

    def test_search_fallback_logs_no_answer(self):
        result = KnowledgeSearchService().search('несуществующий вопрос', self.student)

        self.assertFalse(result['found'])
        self.assertEqual(result['message'], 'Не найден подтвержденный актуальный материал.')
        self.assertEqual(
            InteractionEvent.objects.filter(
                university='Demo University',
                event_type='knowledge_no_answer',
            ).count(),
            1,
        )

    def test_api_keeps_tenant_isolation(self):
        client = APIClient()
        client.force_authenticate(self.other_student)

        response = client.get('/api/knowledge/search?q=производственную практику')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Подайте заявление', str(response.data))
