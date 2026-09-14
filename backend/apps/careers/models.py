from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Skill(models.Model):
    """
    A skill that can be associated with career roles and students.
    Can be university-specific or general.
    """
    CATEGORY_CHOICES = [
        ('technical', 'Technical'),
        ('soft', 'Soft Skills'),
        ('language', 'Language'),
        ('domain', 'Domain Knowledge'),
        ('tool', 'Tools & Software'),
        ('other', 'Other'),
    ]

    university = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Leave blank for general skills available to all universities'
    )
    name = models.CharField(max_length=200)
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='other'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        unique_together = [['university', 'name']]
        indexes = [
            models.Index(fields=['university', 'category']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        if self.university:
            return f"{self.name} ({self.university})"
        return f"{self.name} (General)"


class CareerRole(models.Model):
    """
    A career role/position available at a university.
    """
    university = models.CharField(max_length=255)
    name = models.CharField(max_length=200)
    description = models.TextField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['university', 'name']
        unique_together = [['university', 'name']]
        indexes = [
            models.Index(fields=['university', 'active']),
            models.Index(fields=['active']),
        ]

    def __str__(self):
        return f"{self.name} at {self.university}"

    def calculate_match_score(self, student_profile):
        """
        Calculate how well a student matches this career role based on their skills.
        Returns a score between 0 and 100.
        """
        role_skills = self.required_skills.all()
        if not role_skills.exists():
            return 0

        total_weight = sum(rs.weight for rs in role_skills)
        if total_weight == 0:
            return 0

        earned_score = 0
        for role_skill in role_skills:
            try:
                student_skill = student_profile.skills.get(skill=role_skill.skill)
                level_ratio = student_skill.level / role_skill.required_level
                skill_score = min(level_ratio, 1.0) * role_skill.weight
                earned_score += skill_score
            except:
                continue

        return round((earned_score / total_weight) * 100, 2)


class CareerRoleSkill(models.Model):
    """
    Links a skill to a career role with required level and weight.
    """
    career_role = models.ForeignKey(
        CareerRole,
        on_delete=models.CASCADE,
        related_name='required_skills'
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='career_roles'
    )
    required_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Required skill level (1-5)'
    )
    weight = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0)],
        help_text='Weight/importance of this skill for the role'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-weight', 'skill__name']
        unique_together = [['career_role', 'skill']]
        indexes = [
            models.Index(fields=['career_role', 'required_level']),
        ]

    def __str__(self):
        return f"{self.skill.name} (Level {self.required_level}) for {self.career_role.name}"


class StudentSkill(models.Model):
    """
    Tracks a student's skill level with optional evidence.
    """
    student = models.ForeignKey(
        'profiles.StudentProfile',
        on_delete=models.CASCADE,
        related_name='skills'
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='student_skills'
    )
    level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Student skill level (1-5)'
    )
    evidence = models.TextField(
        blank=True,
        null=True,
        help_text='Optional evidence or documentation of this skill (certifications, projects, etc.)'
    )
    verified = models.BooleanField(
        default=False,
        help_text='Whether this skill has been verified by the university'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student', '-level', 'skill__name']
        unique_together = [['student', 'skill']]
        indexes = [
            models.Index(fields=['student', 'level']),
            models.Index(fields=['skill', 'level']),
            models.Index(fields=['verified']),
        ]

    def __str__(self):
        verified_marker = "✓" if self.verified else ""
        return f"{self.student.user.email} - {self.skill.name} (Level {self.level}){verified_marker}"
