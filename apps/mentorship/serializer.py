from django.contrib.auth.models import User
from rest_framework import serializers

from apps.core.models import UserProfile
from apps.core.serializers import TalentProfileSerializer
from apps.core.serializers_member import CustomUserSerializer, UserProfileSerializer
from apps.mentorship.models import MentorSupportAreas, CommitmentLevel, ApplicationQuestion, MentorProfile, \
    MenteeProfile, ApplicationAnswers, MentorshipProgramProfile, MentorRoster, MentorReview
from apps.talent.models import TalentProfile


class MentorSupportAreasSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorSupportAreas
        fields = ('id', 'name')


class CommitmentLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommitmentLevel
        fields = ['name']


class ApplicationQuestionSerializer(serializers.ModelSerializer):
    # Serializer fields for choices
    mentor_support_areas = MentorSupportAreasSerializer(many=True, read_only=True)
    commitment_levels = CommitmentLevelSerializer(many=True, read_only=True)

    class Meta:
        model = ApplicationQuestion
        fields = '__all__'


class MentorProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    talent_profile = serializers.SerializerMethodField(read_only=True)
    user_profile = serializers.SerializerMethodField(read_only=True)
    mentor_support_areas = MentorSupportAreasSerializer(many=True, read_only=True)

    class Meta:
        model = MentorProfile
        fields = '__all__'

    def get_talent_profile(self, obj):
        # Assuming that there is a reverse relationship from CustomUser to TalentProfile named 'talentprofile'
        talent_profile = TalentProfile.objects.filter(user=obj.user).first()
        return TalentProfileSerializer(talent_profile).data if talent_profile else None

    def get_user_profile(self, obj):
        # Assuming that there is a reverse relationship from CustomUser to TalentProfile named 'talentprofile'
        user_profile = UserProfile.objects.filter(user=obj.user).first()
        return UserProfileSerializer(user_profile).data if user_profile else None


class MenteeProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenteeProfile
        fields = '__all__'


class ApplicationAnswersSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationAnswers
        fields = '__all__'


class MentorshipProgramProfileSerializer(serializers.ModelSerializer):
    mentor_profile = serializers.SerializerMethodField(read_only=True)
    mentee_profile = serializers.SerializerMethodField(read_only=True)
    mentor_support_areas = MentorSupportAreasSerializer(many=True, read_only=True)
    class Meta:
        model = MentorshipProgramProfile
        fields = '__all__'

    def get_mentor_profile(self, obj):
        mentor_profile = MentorProfile.objects.filter(user=obj.user.id).first()
        return MentorProfileSerializer(mentor_profile).data if mentor_profile else None

    def get_mentee_profile(self, obj):
        mentee_profile = MenteeProfile.objects.filter(user=obj.user.id).first()
        return MentorProfileSerializer(mentee_profile).data if mentee_profile else None


class MentorRosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorRoster
        fields = ['mentor', 'mentee', 'mentee_review_of_mentor', 'mentor_review_of_mentee']

    def create(self, validated_data):
        # Additional logic (if needed) before saving the instance
        return MentorRoster.objects.create(**validated_data)


class MentorReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorReview
        fields = ['mentor', 'mentee', 'rating', 'review_content']
