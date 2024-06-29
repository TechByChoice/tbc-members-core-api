from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class BaseUserSerializer(serializers.ModelSerializer):
    """
    Base serializer for User model with common fields.
    """

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class CustomUserSerializer(BaseUserSerializer):
    """
    Serializer for User model with all fields except password.
    """

    class Meta(BaseUserSerializer.Meta):
        exclude = ["password"]


class ReadOnlyCustomUserSerializer(BaseUserSerializer):
    """
    Read-only serializer for User model with additional fields.
    """

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + [
            "is_community_recruiter", "is_member", "is_mentee", "is_mentor",
            "is_mentor_profile_active", "is_mentor_profile_removed", "is_mentor_training_complete",
            "is_mentor_profile_approved", "is_speaker", "is_team", "is_volunteer", "is_mentor_interviewing",
            "is_mentor_profile_paused", "joined_at", "is_active"
        ]


class CustomAuthTokenSerializer(serializers.Serializer):
    """
    Serializer for user authentication tokens.
    """
    email = serializers.EmailField()
    password = serializers.CharField(style={"input_type": "password"}, trim_whitespace=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        user = authenticate(request=self.context.get("request"), username=email, password=password)
        if not user:
            msg = _("Unable to log in with provided credentials.")
            raise serializers.ValidationError(msg, code="authorization")
        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """

    class Meta:
        model = User
        fields = ("password", "email", "first_name", "last_name")
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {
                "required": True,
                "allow_blank": False,
                "validators": [
                    serializers.UniqueValidator(
                        User.objects.all(),
                        "A user with that email already exists",
                    )
                ],
            },
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UpdateCustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for updating custom user fields.
    """

    class Meta:
        model = User
        fields = (
            "is_recruiter", "is_member", "is_mentor", "is_mentee", "is_mentor_profile_active",
            "is_mentor_training_complete", "is_mentor_profile_approved", "is_mentor_application_submitted",
            "is_talent_source_beta", "is_speaker", "is_volunteer", "is_team", "is_community_recruiter",
            "is_company_account", "is_partnership",
        )
