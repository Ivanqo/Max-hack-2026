from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Opportunity, OpportunitySkill, SavedOpportunity, MatchResult

User = get_user_model()


class OpportunitySkillSerializer(serializers.ModelSerializer):
    """Serializer for opportunity skills."""

    class Meta:
        model = OpportunitySkill
        fields = ['id', 'skill', 'required_level', 'weight']
        read_only_fields = ['id']


class OpportunityListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for opportunity lists."""

    required_skills = OpportunitySkillSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    is_saved = serializers.SerializerMethodField()
    match_score = serializers.SerializerMethodField()

    class Meta:
        model = Opportunity
        fields = [
            'id', 'university', 'type', 'title', 'description', 'requirements',
            'audience', 'deadline', 'source_url', 'verified_status', 'published',
            'required_skills', 'created_by_name', 'is_saved', 'match_score',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_saved(self, obj):
        """Check if the current user has saved this opportunity."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedOpportunity.objects.filter(
                student=request.user,
                opportunity=obj
            ).exists()
        return False

    def get_match_score(self, obj):
        """Get the match score for the current user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                match = MatchResult.objects.get(student=request.user, opportunity=obj)
                return match.score
            except MatchResult.DoesNotExist:
                return None
        return None


class OpportunityDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single opportunity view."""

    required_skills = OpportunitySkillSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    is_saved = serializers.SerializerMethodField()
    match_info = serializers.SerializerMethodField()

    class Meta:
        model = Opportunity
        fields = [
            'id', 'university', 'type', 'title', 'description', 'requirements',
            'audience', 'deadline', 'source_url', 'verified_status', 'published',
            'required_skills', 'created_by', 'created_by_name', 'created_by_email',
            'is_saved', 'match_info', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_is_saved(self, obj):
        """Check if the current user has saved this opportunity."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedOpportunity.objects.filter(
                student=request.user,
                opportunity=obj
            ).exists()
        return False

    def get_match_info(self, obj):
        """Get detailed match information for the current user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                match = MatchResult.objects.get(student=request.user, opportunity=obj)
                return {
                    'score': match.score,
                    'reasons': match.reasons,
                    'gaps': match.gaps,
                    'calculated_at': match.calculated_at
                }
            except MatchResult.DoesNotExist:
                return None
        return None


class OpportunityCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating opportunities."""

    required_skills = OpportunitySkillSerializer(many=True, required=False)

    class Meta:
        model = Opportunity
        fields = [
            'id', 'university', 'type', 'title', 'description', 'requirements',
            'audience', 'deadline', 'source_url', 'verified_status', 'published',
            'required_skills', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {'university': {'required': False}}

    def validate_university(self, value):
        """Validate that users can only create opportunities for their own university."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Only admins can create opportunities for any university
            if request.user.role != 'admin':
                if value != request.user.university:
                    raise serializers.ValidationError(
                        "You can only create opportunities for your own university."
                    )
        return value

    def create(self, validated_data):
        """Create opportunity with related skills."""
        skills_data = validated_data.pop('required_skills', [])
        opportunity = Opportunity.objects.create(**validated_data)

        for skill_data in skills_data:
            OpportunitySkill.objects.create(opportunity=opportunity, **skill_data)

        return opportunity

    def update(self, instance, validated_data):
        """Update opportunity and related skills."""
        skills_data = validated_data.pop('required_skills', None)

        # Update opportunity fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update skills if provided
        if skills_data is not None:
            # Clear existing skills
            instance.required_skills.all().delete()
            # Create new skills
            for skill_data in skills_data:
                OpportunitySkill.objects.create(opportunity=instance, **skill_data)

        return instance


class SavedOpportunitySerializer(serializers.ModelSerializer):
    """Serializer for saved opportunities."""

    opportunity = OpportunityListSerializer(read_only=True)
    opportunity_id = serializers.PrimaryKeyRelatedField(
        queryset=Opportunity.objects.all(),
        source='opportunity',
        write_only=True
    )

    class Meta:
        model = SavedOpportunity
        fields = ['id', 'opportunity', 'opportunity_id', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_opportunity_id(self, value):
        """Validate that the opportunity is published and accessible."""
        if not value.published:
            raise serializers.ValidationError("Cannot save unpublished opportunities.")

        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Students can only save opportunities from their university
            if request.user.role == 'student':
                if value.university != request.user.university:
                    raise serializers.ValidationError(
                        "You can only save opportunities from your university."
                    )

        return value


class MatchResultSerializer(serializers.ModelSerializer):
    """Serializer for match results."""

    opportunity = OpportunityListSerializer(read_only=True)

    class Meta:
        model = MatchResult
        fields = [
            'id', 'opportunity', 'score', 'reasons', 'gaps', 'calculated_at'
        ]
        read_only_fields = ['id', 'calculated_at']
