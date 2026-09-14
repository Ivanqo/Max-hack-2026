from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Subscription

User = get_user_model()


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for Subscription model with tenant isolation.
    """
    student_email = serializers.EmailField(source='student.email', read_only=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id',
            'student',
            'student_email',
            'student_name',
            'topic',
            'filters',
            'active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'student', 'created_at', 'updated_at']

    def validate_topic(self, value):
        """Validate topic is not empty and has reasonable length."""
        if not value or not value.strip():
            raise serializers.ValidationError("Topic cannot be empty.")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Topic must be at least 2 characters long.")
        return value.strip()

    def validate_filters(self, value):
        """Validate filters is a valid dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Filters must be a valid JSON object.")
        return value

    def create(self, validated_data):
        """
        Create subscription with the authenticated user as the student.
        Enforces tenant isolation at creation.
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['student'] = request.user
        return super().create(validated_data)


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating subscriptions (excludes read-only fields).
    """
    class Meta:
        model = Subscription
        fields = ['topic', 'filters', 'active']

    def validate_topic(self, value):
        """Validate topic is not empty and has reasonable length."""
        if not value or not value.strip():
            raise serializers.ValidationError("Topic cannot be empty.")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Topic must be at least 2 characters long.")
        return value.strip()

    def validate_filters(self, value):
        """Validate filters is a valid dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Filters must be a valid JSON object.")
        return value

    def create(self, validated_data):
        """
        Create subscription with the authenticated user as the student.
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['student'] = request.user
        return Subscription.objects.create(**validated_data)


class SubscriptionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating subscriptions (limited fields).
    """
    class Meta:
        model = Subscription
        fields = ['topic', 'filters', 'active']

    def validate_topic(self, value):
        """Validate topic is not empty and has reasonable length."""
        if not value or not value.strip():
            raise serializers.ValidationError("Topic cannot be empty.")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Topic must be at least 2 characters long.")
        return value.strip()

    def validate_filters(self, value):
        """Validate filters is a valid dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Filters must be a valid JSON object.")
        return value
