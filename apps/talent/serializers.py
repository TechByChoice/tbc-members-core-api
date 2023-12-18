from rest_framework import serializers

from apps.talent.models import TalentProfile


class UpdateTalentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentProfile
        fields = '__all__'
