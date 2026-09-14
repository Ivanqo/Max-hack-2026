from rest_framework import serializers
from django.utils import timezone
from .models import KnowledgeItem, KnowledgeReport


class KnowledgeItemSerializer(serializers.ModelSerializer):
    """Serializer for KnowledgeItem model."""

    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeItem
        fields = [
            'id',
            'university',
            'title',
            'content',
            'source_url',
            'responsible_unit',
            'audience',
            'verified_status',
            'published',
            'actual_until',
            'created_by',
            'created_by_email',
            'created_at',
            'updated_at',
            'is_current',
        ]
        read_only_fields = ['id', 'created_by', 'created_by_email', 'created_at', 'updated_at', 'is_current']

    def get_is_current(self, obj):
        """Check if knowledge item is still current."""
        return obj.is_current()

    def validate_audience(self, value):
        """Validate audience contains only valid choices."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Audience must be a list.")

        valid_choices = KnowledgeItem.AUDIENCE_CHOICES
        for audience_type in value:
            if audience_type not in valid_choices:
                raise serializers.ValidationError(
                    f"Invalid audience type: {audience_type}. Must be one of {valid_choices}"
                )
        return value

    def validate(self, data):
        """Validate the entire object."""
        # Ensure verified items are published
        if data.get('verified_status') == 'verified' and not data.get('published', True):
            raise serializers.ValidationError(
                "Verified items must be published."
            )
        return data


class KnowledgeItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeItem
        fields = [
            'id',
            'university',
            'title',
            'verified_status',
            'published',
            'actual_until',
            'created_by_email',
            'created_at',
            'is_current',
        ]
        read_only_fields = fields

    def get_is_current(self, obj):
        return obj.is_current()


class KnowledgeItemSearchSerializer(serializers.ModelSerializer):
    """Serializer for search results with rank."""

    rank = serializers.FloatField(read_only=True)
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeItem
        fields = [
            'id',
            'university',
            'title',
            'content',
            'source_url',
            'responsible_unit',
            'audience',
            'verified_status',
            'actual_until',
            'created_at',
            'is_current',
            'rank',
        ]
        read_only_fields = fields

    def get_is_current(self, obj):
        return obj.is_current()


class KnowledgeItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating knowledge items."""

    class Meta:
        model = KnowledgeItem
        fields = [
            'university',
            'title',
            'content',
            'source_url',
            'responsible_unit',
            'audience',
            'verified_status',
            'published',
            'actual_until',
        ]

    def validate_audience(self, value):
        """Validate audience contains only valid choices."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Audience must be a list.")

        valid_choices = KnowledgeItem.AUDIENCE_CHOICES
        for audience_type in value:
            if audience_type not in valid_choices:
                raise serializers.ValidationError(
                    f"Invalid audience type: {audience_type}. Must be one of {valid_choices}"
                )
        return value

    def create(self, validated_data):
        """Create knowledge item with current user as creator."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class KnowledgeReportSerializer(serializers.ModelSerializer):
    """Serializer for KnowledgeReport model."""

    student_email = serializers.EmailField(source='student.email', read_only=True)
    resolved_by_email = serializers.EmailField(source='resolved_by.email', read_only=True)
    knowledge_item_title = serializers.CharField(source='knowledge_item.title', read_only=True)

    class Meta:
        model = KnowledgeReport
        fields = [
            'id',
            'university',
            'student',
            'student_email',
            'knowledge_item',
            'knowledge_item_title',
            'reason',
            'status',
            'resolution_note',
            'resolved_by',
            'resolved_by_email',
            'resolved_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'student',
            'student_email',
            'knowledge_item_title',
            'status',
            'resolution_note',
            'resolved_by',
            'resolved_by_email',
            'resolved_at',
            'created_at',
            'updated_at',
        ]

    def validate(self, data):
        """Ensure knowledge item belongs to same university."""
        knowledge_item = data.get('knowledge_item')
        university = data.get('university')

        if knowledge_item and university:
            if knowledge_item.university != university:
                raise serializers.ValidationError(
                    "Knowledge item must belong to the same university."
                )

        return data


class KnowledgeReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating knowledge reports."""

    class Meta:
        model = KnowledgeReport
        fields = [
            'university',
            'knowledge_item',
            'reason',
        ]

    def validate_knowledge_item(self, value):
        """Ensure knowledge item exists and is published."""
        if not value.published:
            raise serializers.ValidationError("Cannot report unpublished knowledge items.")
        return value

    def validate(self, data):
        """Ensure knowledge item belongs to same university."""
        knowledge_item = data.get('knowledge_item')
        university = data.get('university')

        if knowledge_item and university:
            if knowledge_item.university != university:
                raise serializers.ValidationError(
                    "Knowledge item must belong to the same university."
                )

        # Check for duplicate reports
        request = self.context.get('request')
        if request and request.user:
            existing_report = KnowledgeReport.objects.filter(
                student=request.user,
                knowledge_item=knowledge_item
            ).exists()
            if existing_report:
                raise serializers.ValidationError(
                    "You have already reported this knowledge item."
                )

        return data

    def create(self, validated_data):
        """Create report with current user as student."""
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)


class KnowledgeReportResolveSerializer(serializers.Serializer):
    """Serializer for resolving knowledge reports."""

    action = serializers.ChoiceField(choices=['resolve', 'reject'])
    resolution_note = serializers.CharField(required=False, allow_blank=True, max_length=5000)
