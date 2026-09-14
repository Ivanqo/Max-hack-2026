from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import StudentProfile, CareerGoal

User = get_user_model()


class CareerGoalSerializer(serializers.ModelSerializer):
    """Serializer for CareerGoal model."""

    class Meta:
        model = CareerGoal
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']


class StudentProfileSerializer(serializers.ModelSerializer):
    """Serializer for StudentProfile model."""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    career_goal_details = CareerGoalSerializer(source='career_goal', read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'user',
            'user_email',
            'user_full_name',
            'university',
            'institute',
            'course',
            'program',
            'interests',
            'career_goal',
            'career_goal_details',
            'onboarding_completed',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def validate_course(self, value):
        """Validate course year is between 1 and 6."""
        if value is not None and (value < 1 or value > 6):
            raise serializers.ValidationError("Course year must be between 1 and 6.")
        return value

    def validate_interests(self, value):
        """Validate interests is a list."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Interests must be a list.")
        return value

    def validate_career_goal(self, value):
        """Validate career goal exists and is active."""
        if value and not value.is_active:
            raise serializers.ValidationError("Selected career goal is not active.")
        return value


class StudentProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating student profiles."""

    class Meta:
        model = StudentProfile
        fields = [
            'university',
            'institute',
            'course',
            'program',
            'interests',
            'career_goal',
        ]

    def validate_course(self, value):
        """Validate course year is between 1 and 6."""
        if value is not None and (value < 1 or value > 6):
            raise serializers.ValidationError("Course year must be between 1 and 6.")
        return value

    def validate_interests(self, value):
        """Validate interests is a list."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Interests must be a list.")
        return value

    def create(self, validated_data):
        """Create profile with authenticated user."""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating student profiles."""

    class Meta:
        model = StudentProfile
        fields = [
            'university',
            'institute',
            'course',
            'program',
            'interests',
            'career_goal',
        ]

    def validate_course(self, value):
        """Validate course year is between 1 and 6."""
        if value is not None and (value < 1 or value > 6):
            raise serializers.ValidationError("Course year must be between 1 and 6.")
        return value

    def validate_interests(self, value):
        """Validate interests is a list."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Interests must be a list.")
        return value


class OnboardingCompleteSerializer(serializers.Serializer):
    """Serializer for completing onboarding."""

    completed = serializers.BooleanField(read_only=True, default=True)
    message = serializers.CharField(read_only=True)


class SkillsUpdateSerializer(serializers.Serializer):
    """Serializer for updating skills/interests."""

    interests = serializers.ListField(
        child=serializers.CharField(max_length=255),
        allow_empty=False
    )

    def validate_interests(self, value):
        """Validate interests list."""
        if not value:
            raise serializers.ValidationError("Interests list cannot be empty.")
        if len(value) > 50:
            raise serializers.ValidationError("Maximum 50 interests allowed.")
        return value

    def update(self, instance, validated_data):
        """Update instance interests."""
        instance.interests = validated_data['interests']
        instance.save(update_fields=['interests', 'updated_at'])
        return instance
