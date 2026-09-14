from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Opportunity(models.Model):
    """
    Represents an opportunity for students (internship, vacancy, project, etc.)
    """

    OPPORTUNITY_TYPES = [
        ('internship', 'Internship'),
        ('vacancy', 'Vacancy'),
        ('project', 'Project'),
        ('hackathon', 'Hackathon'),
        ('event', 'Event'),
        ('course', 'Course'),
    ]

    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    university = models.CharField(max_length=255, db_index=True)
    type = models.CharField(max_length=20, choices=OPPORTUNITY_TYPES, db_index=True)
    title = models.CharField(max_length=500)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    audience = models.JSONField(
        default=dict,
        help_text="Target audience criteria (e.g., year, major, skills)"
    )
    deadline = models.DateTimeField(null=True, blank=True, db_index=True)
    source_url = models.URLField(max_length=1000, blank=True)
    verified_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='pending',
        db_index=True
    )
    published = models.BooleanField(default=False, db_index=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_opportunities'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Opportunity'
        verbose_name_plural = 'Opportunities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['university', 'type']),
            models.Index(fields=['published', 'verified_status']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_type_display()})"


class OpportunitySkill(models.Model):
    """
    Links opportunities to required skills with proficiency levels
    """

    SKILL_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]

    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='required_skills'
    )
    skill = models.CharField(max_length=200, db_index=True)
    required_level = models.CharField(
        max_length=20,
        choices=SKILL_LEVELS,
        default='intermediate'
    )
    weight = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Importance weight (1-10)"
    )

    class Meta:
        verbose_name = 'Opportunity Skill'
        verbose_name_plural = 'Opportunity Skills'
        unique_together = ['opportunity', 'skill']
        ordering = ['-weight', 'skill']

    def __str__(self):
        return f"{self.skill} ({self.required_level}) for {self.opportunity.title}"


class SavedOpportunity(models.Model):
    """
    Tracks opportunities saved/bookmarked by students
    """

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_opportunities'
    )
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='saved_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Saved Opportunity'
        verbose_name_plural = 'Saved Opportunities'
        unique_together = ['student', 'opportunity']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', '-created_at']),
        ]

    def __str__(self):
        name = self.student.username or self.student.email
        return f"{name} saved {self.opportunity.title}"


class MatchResult(models.Model):
    """
    Stores calculated match scores between students and opportunities
    """

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='opportunity_matches'
    )
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='student_matches'
    )
    score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Match score from 0 to 100"
    )
    reasons = models.JSONField(
        default=list,
        help_text="List of reasons why this opportunity matches"
    )
    gaps = models.JSONField(
        default=list,
        help_text="List of skill/requirement gaps"
    )
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Match Result'
        verbose_name_plural = 'Match Results'
        unique_together = ['student', 'opportunity']
        ordering = ['-score', '-calculated_at']
        indexes = [
            models.Index(fields=['student', '-score']),
            models.Index(fields=['opportunity', '-score']),
            models.Index(fields=['-calculated_at']),
        ]

    def __str__(self):
        name = self.student.username or self.student.email
        return f"{name} - {self.opportunity.title}: {self.score}%"
