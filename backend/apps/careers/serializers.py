from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Skill, CareerRole, CareerRoleSkill, StudentSkill


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for Skill model."""

    class Meta:
        model = Skill
        fields = [
            'id', 'university', 'name', 'category',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        """Ensure skills are scoped to the correct university."""
        request = self.context.get('request')
        if request and hasattr(request.user, 'university'):
            attrs['university'] = request.user.university
        return attrs


class CareerRoleSkillSerializer(serializers.ModelSerializer):
    """Serializer for CareerRoleSkill model."""
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    skill_category = serializers.CharField(source='skill.category', read_only=True)

    class Meta:
        model = CareerRoleSkill
        fields = [
            'id', 'skill', 'skill_name', 'skill_category',
            'required_level', 'weight', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_required_level(self, value):
        """Validate required level is between 1 and 5."""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Required level must be between 1 and 5")
        return value

    def validate_weight(self, value):
        """Validate weight is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Weight must be non-negative")
        return value


class CareerRoleSerializer(serializers.ModelSerializer):
    """Serializer for CareerRole model."""
    required_skills = CareerRoleSkillSerializer(many=True, read_only=True)
    skills_count = serializers.SerializerMethodField()

    class Meta:
        model = CareerRole
        fields = [
            'id', 'university', 'name', 'description', 'active',
            'required_skills', 'skills_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_skills_count(self, obj):
        """Get the count of required skills."""
        return obj.required_skills.count()

    def validate(self, attrs):
        """Ensure career roles are scoped to the correct university."""
        request = self.context.get('request')
        if request and hasattr(request.user, 'university'):
            attrs['university'] = request.user.university
        return attrs


class CareerRoleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing career roles."""
    skills_count = serializers.SerializerMethodField()

    class Meta:
        model = CareerRole
        fields = [
            'id', 'university', 'name', 'active',
            'skills_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_skills_count(self, obj):
        """Get the count of required skills."""
        return obj.required_skills.count()


class StudentSkillSerializer(serializers.ModelSerializer):
    """Serializer for StudentSkill model."""
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    skill_category = serializers.CharField(source='skill.category', read_only=True)
    student_email = serializers.EmailField(source='student.user.email', read_only=True)

    class Meta:
        model = StudentSkill
        fields = [
            'id', 'student', 'student_email', 'skill', 'skill_name',
            'skill_category', 'level', 'evidence', 'verified',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'verified', 'created_at', 'updated_at']

    def validate_level(self, value):
        """Validate level is between 1 and 5."""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Level must be between 1 and 5")
        return value

    def validate(self, attrs):
        """Ensure students can only manage their own skills."""
        request = self.context.get('request')
        if request and hasattr(request.user, 'student_profile'):
            attrs['student'] = request.user.student_profile
        return attrs


class CareerMatchSerializer(serializers.Serializer):
    """Serializer for career role match calculation."""
    career_role_id = serializers.IntegerField()
    career_role_name = serializers.CharField()
    match_score = serializers.FloatField()
    required_skills_count = serializers.IntegerField()
    matched_skills_count = serializers.IntegerField()
    university = serializers.CharField()


class GPSCalculationSerializer(serializers.Serializer):
    """Serializer for GPS (Goal Progress Score) calculation request."""
    student_id = serializers.IntegerField(required=False)
    career_role_id = serializers.IntegerField(required=False)

    def validate_student_id(self, value):
        """Validate student exists if provided."""
        from apps.profiles.models import StudentProfile
        if value and not StudentProfile.objects.filter(user_id=value).exists():
            raise serializers.ValidationError("Student profile not found")
        return value


class GPSResultSerializer(serializers.Serializer):
    """Serializer for GPS calculation result."""
    student_id = serializers.IntegerField()
    student_email = serializers.EmailField()
    overall_score = serializers.FloatField()
    top_matches = CareerMatchSerializer(many=True)
    total_skills = serializers.IntegerField()
    verified_skills = serializers.IntegerField()
    calculated_at = serializers.DateTimeField()
