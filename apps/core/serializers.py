from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers, validators
from rest_framework.authtoken.serializers import AuthTokenSerializer

from apps.company.models import CompanyProfile, Roles, Department
from apps.company.serializers import RoleSerializer, SkillSerializer
from apps.core.models import UserProfile, CustomUser
from apps.member.models import MemberProfile


class CustomAuthTokenSerializer(AuthTokenSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={"input_type": "password"}, trim_whitespace=True
    )

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(
                request=self.context.get("request"), username=email, password=password
            )

            # The authenticate call simply returns None for is_active=False
            # users. (Assuming the default ModelBackend authentication
            # backend.)
            if not user:
                msg = _("Unable to log in with provided credentials.")
                raise serializers.ValidationError(msg, code="authorization")
        else:
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("password", "email", "first_name", "last_name")

        extra_kwargs = {
            "password": {"write_only": True},
            "email": {
                "required": True,
                "allow_blank": False,
                "validators": [
                    validators.UniqueValidator(
                        CustomUser.objects.all(),
                        "A user with that email already exists",
                    )
                ],
            },
        }

    def create(self, validated_data):
        password = validated_data.get("password")
        email = validated_data.get("email")
        first_name = validated_data.get("first_name")
        last_name = validated_data.get("last_name")

        user = CustomUser.objects.create_user(
            email=email, password=password, first_name=first_name, last_name=last_name
        )
        return user


class UpdateCustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = (
            "is_recruiter",
            "is_member",
            "is_mentor",
            "is_mentee",
            "is_mentor_profile_active",
            "is_mentor_training_complete",
            "is_mentor_profile_approved",
            "is_mentor_application_submitted",
            "is_talent_source_beta",
            "is_speaker",
            "is_volunteer",
            "is_team",
            "is_community_recruiter",
            "is_company_account",
            "is_partnership",
        )


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = "__all__"


class UpdateProfileAccountDetailsSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.EmailField(source="user.email")
    postal_code = serializers.CharField()
    location = serializers.CharField()
    state = serializers.CharField()
    city = serializers.CharField()

    class Meta:
        model = MemberProfile
        fields = ["first_name", "last_name", "email", "postal_code", "location", "state", "city"]

    def update(self, instance, validated_data):
        # Extracting user related data
        user_data = validated_data.pop("user", {})
        instance.postal_code = validated_data.get("postal_code", instance.postal_code)
        instance.location = validated_data.get("location", instance.location)
        instance.state = validated_data.get("state", instance.state)
        instance.city = validated_data.get("city", instance.city)
        instance.save()
        # Updating user instance related fields
        user_instance = instance.user
        member_profile = user_instance.userprofile
        user_instance.first_name = user_data.get("first_name", user_instance.first_name)
        user_instance.last_name = user_data.get("last_name", user_instance.last_name)
        user_instance.email = user_data.get("email", user_instance.email)
        member_profile.location = validated_data.get("location", instance.location)
        member_profile.state = validated_data.get("state", instance.state)
        member_profile.city = validated_data.get("city", instance.city)


        user_instance.save()
        instance.save()

        return instance


class CompanyProfileSerializer(serializers.ModelSerializer):
    current_employees = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), many=True, required=False
    )
    company_name = serializers.CharField(required=False, allow_blank=True)
    company_url = serializers.URLField(required=False, allow_blank=True)

    class Meta:
        model = CompanyProfile
        fields = ["id", "company_name", "company_url", "current_employees"]

    def create(self, validated_data):
        user = self.context["request"].user  # get the user from the request context
        company_name = validated_data.get("company_name", None)
        company_url = validated_data.get("company_url", None)

        # Only create a new company if both company_name and company_url are provided.
        if not company_name or not company_url:
            raise serializers.ValidationError(
                "Both company_name and company_url must be provided for new companies."
            )

        company = CompanyProfile.objects.create(**validated_data)
        company.current_employees.add(user)
        company.save()

        return company


class TalentProfileRoleSerializer(serializers.ModelSerializer):
    role = serializers.PrimaryKeyRelatedField(queryset=Roles.objects.all(), many=True)

    class Meta:
        model = MemberProfile
        fields = ["role"]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ("id", "name")


class TalentProfileSerializer(serializers.ModelSerializer):
    role = RoleSerializer(many=True, read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    department = DepartmentSerializer(many=True, read_only=True)

    class Meta:
        model = MemberProfile
        fields = "__all__"
