from rest_framework import serializers
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import InteractionEvent, AuditLog


class InteractionEventSerializer(serializers.ModelSerializer):
    """Serializer for interaction events."""

    user_email = serializers.EmailField(source='user.email', read_only=True, allow_null=True)

    class Meta:
        model = InteractionEvent
        fields = [
            'id', 'university', 'user', 'user_email', 'event_type',
            'entity_type', 'entity_id', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'user_email']

    def validate_university(self, value):
        """Ensure university is provided and not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("University identifier is required.")
        return value.strip()


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs."""

    admin_email = serializers.EmailField(source='admin.email', read_only=True, allow_null=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'university', 'admin', 'admin_email', 'action',
            'entity_type', 'entity_id', 'metadata', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp', 'admin_email']

    def validate_university(self, value):
        """Ensure university is provided and not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("University identifier is required.")
        return value.strip()


class TopQuerySerializer(serializers.Serializer):
    """Serializer for top search queries."""

    query = serializers.CharField()
    count = serializers.IntegerField()
    last_searched = serializers.DateTimeField()


class UnansweredQuerySerializer(serializers.Serializer):
    """Serializer for unanswered queries (searches with no results)."""

    query = serializers.CharField()
    count = serializers.IntegerField()
    first_searched = serializers.DateTimeField()
    last_searched = serializers.DateTimeField()


class OverviewStatsSerializer(serializers.Serializer):
    """Serializer for overview analytics statistics."""

    total_interactions = serializers.IntegerField()
    total_users = serializers.IntegerField()
    total_searches = serializers.IntegerField()
    total_views = serializers.IntegerField()
    total_clicks = serializers.IntegerField()
    total_saves = serializers.IntegerField()
    total_applies = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    active_users_week = serializers.IntegerField()
    active_users_month = serializers.IntegerField()
    popular_entity_types = serializers.DictField(child=serializers.IntegerField())
    event_type_distribution = serializers.DictField(child=serializers.IntegerField())
    time_range_start = serializers.DateTimeField()
    time_range_end = serializers.DateTimeField()


class EventTypeCountSerializer(serializers.Serializer):
    """Serializer for event type counts."""

    event_type = serializers.CharField()
    count = serializers.IntegerField()


class EntityTypeCountSerializer(serializers.Serializer):
    """Serializer for entity type counts."""

    entity_type = serializers.CharField()
    count = serializers.IntegerField()
