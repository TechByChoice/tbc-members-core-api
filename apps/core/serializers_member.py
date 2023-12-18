from rest_framework import serializers
from .models import CustomUser, UserProfile
from ..talent.models import TalentProfile


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'


class TalentProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = TalentProfile
        fields = '__all__'
