from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.careers.models import CareerRole, CareerRoleSkill, Skill, StudentSkill
from apps.careers.services import CareerGPSService
from apps.profiles.models import CareerGoal, StudentProfile


class CareerGPSServiceTest(TestCase):
    def test_calculates_strengths_gaps_and_score(self):
        User = get_user_model()
        student = User.objects.create_user(
            email='gps@test.local',
            password='pass12345',
            role='student',
            university='Demo University',
        )
        goal = CareerGoal.objects.create(name='Backend Developer')
        profile = StudentProfile.objects.create(
            user=student,
            university='Demo University',
            institute='Institute of Computer Science',
            course=3,
            program='Software Engineering',
            career_goal=goal,
            onboarding_completed=True,
        )
        python = Skill.objects.create(university='Demo University', name='Python', category='technical')
        docker = Skill.objects.create(university='Demo University', name='Docker', category='tool')
        role = CareerRole.objects.create(
            university='Demo University',
            name='Backend Developer',
            description='Build APIs.',
        )
        CareerRoleSkill.objects.create(career_role=role, skill=python, required_level=4, weight=2)
        CareerRoleSkill.objects.create(career_role=role, skill=docker, required_level=3, weight=1)
        StudentSkill.objects.create(student=profile, skill=python, level=4)

        result = CareerGPSService().calculate(profile, role)

        self.assertEqual(result['readiness_score'], 67)
        self.assertTrue(result['strengths'])
        self.assertEqual(result['gaps'][0]['skill'], 'Docker')
        self.assertTrue(result['next_actions'])
