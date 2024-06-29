from rest_framework import serializers
from apps.core.models import UserProfile, CommunityNeeds
from apps.member.models import MemberProfile


class BaseUserProfileSerializer(serializers.ModelSerializer):
    """
    Base serializer for UserProfile model.
    """
    identity_pronouns = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')

    class Meta:
        model = UserProfile
        fields = "__all__"

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        hidden_fields = [
            ("identity_sexuality", "is_identity_sexuality_displayed"),
            ("identity_gender", "is_identity_gender_displayed"),
            ("identity_ethic", "is_identity_ethic_displayed"),
            ("identity_pronouns", "is_pronouns_displayed"),
            ("disability", "is_disability_displayed"),
            ("care_giver", "is_care_giver_displayed"),
            ("veteran_status", "is_veteran_status_displayed"),
        ]
        for field, display_field in hidden_fields:
            if not getattr(instance, display_field):
                ret.pop(field, None)
        return ret


class UserProfileSerializer(BaseUserProfileSerializer):
    """
    Serializer for UserProfile model with additional tbc_program_interest field.
    """
    tbc_program_interest = serializers.SerializerMethodField()

    def get_tbc_program_interest(self, obj):
        return CommunityNeedsSerializer(obj.tbc_program_interest.all(), many=True).data


class ReadOnlyUserProfileSerializer(BaseUserProfileSerializer):
    """
    Read-only serializer for UserProfile model with specific fields excluded.
    """

    class Meta(BaseUserProfileSerializer.Meta):
        exclude = ['access_token', 'how_connection_made', 'is_terms_agree', 'marketing_events', 'marketing_jobs',
                   'marketing_org_updates', 'marketing_monthly_newsletter', 'marketing_identity_based_programing',
                   'tbc_program_interest']


class UpdateProfileAccountDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for updating profile account details.
    """
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = MemberProfile
        fields = ["first_name", "last_name", "email", "postal_code", "location", "state", "city"]

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        user_instance = instance.user
        member_profile = user_instance.userprofile
        for attr, value in user_data.items():
            setattr(user_instance, attr, value)
            setattr(member_profile, attr, value)
        user_instance.save()
        member_profile.save()

        return instance

