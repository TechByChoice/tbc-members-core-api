from rest_framework import serializers
from ..models import MentorProfile, MenteeProfile, MentorRoster, Session, MentorSupportAreas, CustomUser


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class MentorSupportAreasSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorSupportAreas
        fields = ['id', 'name']


class MentorProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)

    class Meta:
        model = MentorProfile
        fields = ['id', 'user', 'mentor_status', 'activated_at_date', 'mentor_commitment_level', 'mentor_how_to_help',
                  'mentorship_goals']


class MenteeProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)

    class Meta:
        model = MenteeProfile
        fields = ['id', 'user', 'activated_at_date', 'commitment_level', 'mentee_support_areas']


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['id', 'mentor_mentee_connection', 'created_by', 'reason', 'note', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        return Session.objects.create(**validated_data)


class MentorRosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorRoster
        fields = ['id', 'mentor', 'mentee']

    def create(self, validated_data):
        return MentorRoster.objects.create(**validated_data)


class MentorMenteeConnectionSerializer(serializers.Serializer):
    mentor_id = serializers.IntegerField()
    mentor_support_areas = serializers.ListField(child=serializers.IntegerField(), required=False)
    mentor_booking_note = serializers.CharField(max_length=500, required=False)

    def validate_mentor_id(self, value):
        try:
            MentorProfile.objects.get(user_id=value)
        except MentorProfile.DoesNotExist:
            raise serializers.ValidationError("Invalid mentor ID")
        return value
