from rest_framework import serializers
from .models import CustomUser, UserProfile
from .util import get_current_company_data
from ..member.models import MemberProfile


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        exclude = ["password"]


class ReadOnlyCustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "is_community_recruiter", "is_member", "is_mentee", "is_mentor",
                  "is_mentor_profile_active", "is_mentor_profile_approved", "is_speaker", "is_team", "is_volunteer",
                  "joined_at", "is_active", "id"]


class UserProfileSerializer(serializers.ModelSerializer):
    identity_pronouns = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )

    class Meta:
        model = UserProfile
        fields = "__all__"

    def to_representation(self, instance):
        ret = super(UserProfileSerializer, self).to_representation(instance)

        if not instance.is_identity_sexuality_displayed:
            ret.pop("identity_sexuality", None)

        if not instance.is_identity_gender_displayed:
            ret.pop("identity_gender", None)

        if not instance.is_identity_ethic_displayed:
            ret.pop("identity_ethic", None)

        if not instance.is_pronouns_displayed:
            ret.pop("identity_pronouns", None)

        if not instance.is_disability_displayed:
            ret.pop("disability", None)

        if not instance.is_care_giver_displayed:
            ret.pop("care_giver", None)

        if not instance.is_veteran_status_displayed:
            ret.pop("veteran_status", None)

        return ret


class ReadOnlyUserProfileSerializer(serializers.ModelSerializer):
    identity_pronouns = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )

    class Meta:
        model = UserProfile
        exclude = ['access_token', 'how_connection_made', 'is_terms_agree', 'marketing_events', 'marketing_jobs',
                   'marketing_org_updates', 'marketing_monthly_newsletter', 'marketing_identity_based_programing',
                   'tbc_program_interest']

    def to_representation(self, instance):
        ret = super(ReadOnlyUserProfileSerializer, self).to_representation(instance)

        if not instance.is_identity_sexuality_displayed:
            ret.pop("identity_sexuality", None)

        if not instance.is_identity_gender_displayed:
            ret.pop("identity_gender", None)

        if not instance.is_identity_ethic_displayed:
            ret.pop("identity_ethic", None)

        if not instance.is_pronouns_displayed:
            ret.pop("identity_pronouns", None)

        if not instance.is_disability_displayed:
            ret.pop("disability", None)

        if not instance.is_care_giver_displayed:
            ret.pop("care_giver", None)

        if not instance.is_veteran_status_displayed:
            ret.pop("veteran_status", None)

        return ret


class TalentProfileSerializer(serializers.ModelSerializer):
    skills = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )
    department = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )
    role = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )
    tech_journey_display = serializers.CharField(source='get_tech_journey_display', read_only=True)

    class Meta:
        model = MemberProfile
        fields = "__all__"


class ReadOnlyTalentProfileSerializer(serializers.ModelSerializer):
    skills = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )
    department = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )
    role = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )
    tech_journey_display = serializers.CharField(source='get_tech_journey_display', read_only=True)

    class Meta:
        model = MemberProfile
        exclude = ["company_types", "created_at", "is_talent_status", "resume"]


class FullTalentProfileSerializer(serializers.ModelSerializer):
    user = ReadOnlyCustomUserSerializer(read_only=True)
    talent_profile = serializers.SerializerMethodField(read_only=True)
    user_profile = serializers.SerializerMethodField(read_only=True)
    company_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MemberProfile
        fields = "__all__"

    def get_talent_profile(self, obj):
        talent_profile = MemberProfile.objects.filter(user=obj.user).first()
        return ReadOnlyTalentProfileSerializer(talent_profile).data if talent_profile else None

    def get_user_profile(self, obj):
        user_profile = UserProfile.objects.filter(user=obj.user).first()
        return ReadOnlyUserProfileSerializer(user_profile).data if user_profile else None

    def get_company_details(selfself, obj):
        return get_current_company_data(user=obj.user)
