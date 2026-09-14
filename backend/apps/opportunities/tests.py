from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.careers.models import Skill, StudentSkill
from apps.opportunities.models import Opportunity, OpportunitySkill, SavedOpportunity
from apps.opportunities.services import OpportunityMatchingService
from apps.profiles.models import StudentProfile


class OpportunityMatchingServiceTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.student = User.objects.create_user(
            email='match@test.local',
            password='pass12345',
            role='student',
            university='Demo University',
        )
        self.profile = StudentProfile.objects.create(
            user=self.student,
            university='Demo University',
            institute='Institute of Computer Science',
            course=3,
            program='Software Engineering',
            interests=['Backend', 'Python'],
            onboarding_completed=True,
        )
        python = Skill.objects.create(university='Demo University', name='Python', category='technical')
        StudentSkill.objects.create(student=self.profile, skill=python, level=4)
        self.opportunity = Opportunity.objects.create(
            university='Demo University',
            type='internship',
            title='Backend Internship',
            description='Python backend work.',
            requirements='Python\nDocker',
            audience={'courses': [3], 'company': 'MAX Labs'},
            verified_status='verified',
            published=True,
        )
        OpportunitySkill.objects.create(
            opportunity=self.opportunity,
            skill='Python',
            required_level='intermediate',
            weight=2,
        )
        OpportunitySkill.objects.create(
            opportunity=self.opportunity,
            skill='Docker',
            required_level='intermediate',
            weight=1,
        )

    def test_matching_is_explainable(self):
        result = OpportunityMatchingService().calculate_for_user(self.student, self.opportunity)

        self.assertGreater(result['score'], 50)
        self.assertIn('Подходит Python', result['reasons'])
        self.assertTrue(any('Docker' in gap for gap in result['gaps']))

    def test_student_opportunities_are_tenant_scoped_and_saveable(self):
        Opportunity.objects.create(
            university='Other University',
            type='internship',
            title='Other Tenant Internship',
            description='Hidden.',
            verified_status='verified',
            published=True,
        )
        client = APIClient()
        client.force_authenticate(self.student)

        response = client.get('/api/student/opportunities')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Backend Internship')
        self.assertIn('matchPercentage', response.data[0])

        save_response = client.post(f'/api/student/opportunities/{self.opportunity.id}/save')
        self.assertEqual(save_response.status_code, 200)
        self.assertTrue(SavedOpportunity.objects.filter(student=self.student, opportunity=self.opportunity).exists())
