from rest_framework import serializers

from apps.company.models import CompanyProfile, InitialHiringNeeds, Job, Department, Skill, Roles, SalaryRange
from apps.core.models import CustomUser, UserProfile


class APIKeySerializer(serializers.Serializer):
    api_key = serializers.CharField(max_length=255)


class CompanySignUpSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('password', 'first_name', 'last_name', 'email', 'company_name')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        company_name = validated_data.pop('company_name')

        # Create CustomUser object
        user = CustomUser.objects.create(**validated_data)

        # Create CompanyProfile object
        user_profile = UserProfile.objects.create(
            user=user
        )
        # Create CompanyProfile object
        company_profile = CompanyProfile.objects.create(
            company_name=company_name,
            account_creator=user
        )
        company_profile.account_owner.set([user]),
        company_profile.billing_team.set([user]),
        company_profile.hiring_team.set([user]),
        company_profile.save(),

        return user


class CompanyOpenRolesSerializer(serializers.ModelSerializer):
    job_roles = serializers.ListField(child=serializers.CharField())
    job_location = serializers.CharField()
    job_site = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = InitialHiringNeeds
        fields = ['company', 'job_roles', 'job_location', 'job_site']


class JobReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            'job_title', 'id', 'external_description', 'level', 'url',
            'external_interview_process', 'status', 'is_referral_job',
            'job_type', 'department', 'skills', 'on_site_remote',
            'min_compensation', 'max_compensation', 'parent_company',
            'role', 'experience', 'years_of_experience', 'location',
            'created_by', 'created_by_id'
        ]

    def create(self, validated_data):
        validated_data['is_referral_job'] = True
        return super(JobReferralSerializer, self).create(validated_data)


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('id', 'name')


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'name', 'skill_type')


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = ('id', 'name')


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = ('id', 'company_name', 'company_url', 'logo', 'industries')


class SalaryRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryRange
        fields = ('id', 'range')


class JobSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(many=True, read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    role = RoleSerializer(read_only=True)
    parent_company = CompanyProfileSerializer(read_only=True)
    min_compensation = SalaryRangeSerializer(read_only=True)
    max_compensation = SalaryRangeSerializer(read_only=True)

    class Meta:
        model = Job
        fields = [
            'id', 'job_title', 'external_description', 'level', 'url', 'external_interview_process',
            'job_type', 'department', 'skills', 'on_site_remote', 'status',
            'compensation_range', 'min_compensation', 'max_compensation',
            'role', 'experience', 'years_of_experience', 'location',
            'team_size', 'female_team_size_total', 'poc_team_size_total',
            'black_team_size_total', 'indigenous_team_size_total',
            'lgbtqia_team_size_total', 'disabled_team_size_total',
            'department_size', 'female_department_size_total',
            'poc_department_size_total', 'black_department_size_total',
            'indigenous_department_size_total', 'lgbtqia_department_size_total',
            'disabled_department_size_total', 'is_paid', 'parent_company',
            'is_remote', 'is_referral_job', 'created_by', 'created_by_id', 'created_at', 'updated_at'
        ]
