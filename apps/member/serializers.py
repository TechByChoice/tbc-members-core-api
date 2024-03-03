from rest_framework import serializers

from apps.member.models import MemberProfile


class UpdateTalentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberProfile
        fields = "__all__"
