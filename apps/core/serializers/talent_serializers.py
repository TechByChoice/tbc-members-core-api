from rest_framework import serializers
from apps.member.models import MemberProfile
from .user_serializers import ReadOnlyCustomUserSerializer
from .profile_serializers import ReadOnlyUserProfileSerializer


class BaseTalentProfileSerializer(serializers.ModelSerializer):
    """
    Base serializer for MemberProfile model.
    """
    skills = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')
    department = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')
    role = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')
    tech_journey_display = serializers.CharField(source='get_tech_journey_display', read_only=True)

    class Meta:
        model = MemberProfile
        fields = "__all__"


class TalentProfileSerializer(BaseTalentProfileSerializer):
    """
    Serializer for MemberProfile model with all fields.
    """
    pass


class ReadOnlyTalentProfileSerializer(BaseTalentProfileSerializer):
    """
    Read-only serializer for MemberProfile model with specific fields excluded.
    """

    class Meta(BaseTalentProfileSerializer.Meta):
        exclude = ["company_types", "created_at", "is_talent_status", "resume"]


class FullTalentProfileSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for MemberProfile model including related data.
    """
    user = ReadOnlyCustomUserSerializer(read_only=True)
    talent_profile = serializers.SerializerMethodField()
    user_profile = serializers.SerializerMethodField()
    company_details = serializers.SerializerMethodField()

    class Meta:
        model = MemberProfile
        fields = "__all__"

    def get_talent_profile(self, obj):
        talent_profile = MemberProfile.objects.filter(user=obj.user).first()
        return ReadOnlyTalentProfileSerializer(talent_profile).data if talent_profile else None

    def get_user_profile(self, obj):
        user_profile = UserProfile.objects.filter(user=obj.user).first()
        return ReadOnlyUserProfileSerializer(user_profile).data if user_profile else None

    def get_company_details(self, obj):
        from apps.core.util import get_current_company_data
        return get_current_company_data(user=obj.user)
