from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""

    student_email = serializers.EmailField(source='student.email', read_only=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    opportunity_title = serializers.CharField(source='opportunity.title', read_only=True, allow_null=True)
    opportunity_type = serializers.CharField(source='opportunity.get_type_display', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'student',
            'student_email',
            'student_name',
            'title',
            'message',
            'opportunity',
            'opportunity_title',
            'opportunity_type',
            'status',
            'status_display',
            'created_at',
            'sent_at',
        ]
        read_only_fields = ['id', 'created_at', 'sent_at', 'status']


class NotificationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing notifications."""

    opportunity_title = serializers.CharField(source='opportunity.title', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'opportunity_title',
            'status',
            'status_display',
            'created_at',
            'sent_at',
        ]
        read_only_fields = fields


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications."""

    class Meta:
        model = Notification
        fields = [
            'student',
            'title',
            'message',
            'opportunity',
        ]

    def validate(self, data):
        """Validate notification data."""
        if not data.get('title'):
            raise serializers.ValidationError({'title': 'Title is required'})

        if not data.get('message'):
            raise serializers.ValidationError({'message': 'Message is required'})

        if len(data.get('title', '')) > 255:
            raise serializers.ValidationError({'title': 'Title must be 255 characters or less'})

        return data
