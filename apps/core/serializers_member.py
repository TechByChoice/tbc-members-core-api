from rest_framework import serializers
from .models import CustomUser, UserProfile
from ..talent.models import TalentProfile


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        exclude = ['password']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
    def to_representation(self, instance):
        ret = super(UserProfileSerializer, self).to_representation(instance)

        if not instance.is_identity_sexuality_displayed:
            ret.pop('identity_sexuality', None)

        if not instance.is_identity_gender_displayed:
            ret.pop('identity_gender', None)

        if not instance.is_identity_ethic_displayed:
            ret.pop('identity_ethic', None)

        if not instance.is_pronouns_displayed:
            ret.pop('identity_pronouns', None)

        if not instance.is_disability_displayed:
            ret.pop('disability', None)

        if not instance.is_care_giver_displayed:
            ret.pop('care_giver', None)

        if not instance.is_veteran_status_displayed:
            ret.pop('veteran_status', None)

        return ret


class TalentProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = TalentProfile
        fields = '__all__'
