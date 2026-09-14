from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import StudentProfile, CareerGoal

User = get_user_model()


class CareerGoalModelTest(TestCase):
    """Test cases for CareerGoal model."""

    def setUp(self):
        self.career_goal = CareerGoal.objects.create(
            name='Software Development',
            description='Build and maintain software applications'
        )

    def test_career_goal_creation(self):
        """Test career goal is created correctly."""
        self.assertEqual(self.career_goal.name, 'Software Development')
        self.assertTrue(self.career_goal.is_active)

    def test_career_goal_str(self):
        """Test string representation."""
        self.assertEqual(str(self.career_goal), 'Software Development')


class StudentProfileModelTest(TestCase):
    """Test cases for StudentProfile model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='student@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.career_goal = CareerGoal.objects.create(
            name='Data Science'
        )

    def test_student_profile_creation(self):
        """Test student profile is created correctly."""
        profile = StudentProfile.objects.create(
            user=self.user,
            university='MIT',
            institute='Computer Science',
            course=3,
            program='Computer Science',
            interests=['Python', 'Machine Learning'],
            career_goal=self.career_goal
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.university, 'MIT')
        self.assertFalse(profile.onboarding_completed)

    def test_filter_by_university(self):
        """Test filtering profiles by university."""
        StudentProfile.objects.create(
            user=self.user,
            university='MIT'
        )
        profiles = StudentProfile.objects.filter_by_university('MIT')
        self.assertEqual(profiles.count(), 1)

    def test_complete_onboarding(self):
        """Test completing onboarding."""
        profile = StudentProfile.objects.create(user=self.user)
        self.assertFalse(profile.onboarding_completed)
        profile.complete_onboarding()
        self.assertTrue(profile.onboarding_completed)

    def test_profile_str(self):
        """Test string representation."""
        profile = StudentProfile.objects.create(
            user=self.user,
            university='MIT'
        )
        self.assertIn(self.user.email, str(profile))
