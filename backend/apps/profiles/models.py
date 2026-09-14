from django.db import models
from django.conf import settings


class CareerGoal(models.Model):
    """Career goal options for students."""

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Career Goal'
        verbose_name_plural = 'Career Goals'
        ordering = ['name']

    def __str__(self):
        return self.name


class StudentProfileManager(models.Manager):
    """Custom manager for StudentProfile model."""

    def filter_by_university(self, university_name):
        """Filter profiles by university name."""
        return self.filter(university__iexact=university_name)

    def completed_onboarding(self):
        """Return profiles that have completed onboarding."""
        return self.filter(onboarding_completed=True)

    def pending_onboarding(self):
        """Return profiles that haven't completed onboarding."""
        return self.filter(onboarding_completed=False)


class StudentProfile(models.Model):
    """Extended profile information for student users."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        primary_key=True
    )
    university = models.CharField(max_length=255, blank=True)
    institute = models.CharField(max_length=255, blank=True)
    course = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text='Year of study (1-6)'
    )
    program = models.CharField(
        max_length=255,
        blank=True,
        help_text='Study program or major'
    )
    interests = models.JSONField(
        default=list,
        blank=True,
        help_text='List of student interests and skills'
    )
    career_goal = models.ForeignKey(
        CareerGoal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    onboarding_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = StudentProfileManager()

    class Meta:
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['university']),
            models.Index(fields=['onboarding_completed']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.university or 'No University'}"

    def complete_onboarding(self):
        """Mark onboarding as completed."""
        self.onboarding_completed = True
        self.save(update_fields=['onboarding_completed', 'updated_at'])
