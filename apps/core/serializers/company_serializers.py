# TODO | CODE CLEAN UP: SHOULD BE MOVED TO COMPANY.SERIALIZERS

from rest_framework import serializers
from apps.company.models import CompanyProfile
from apps.core.models import CustomUser


class CompanyProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for CompanyProfile model.
    """
    current_employees = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), many=True, required=False)

    class Meta:
        model = CompanyProfile
        fields = ["id", "company_name", "company_url", "current_employees"]
        extra_kwargs = {
            'company_name': {'required': False, 'allow_blank': True},
            'company_url': {'required': False, 'allow_blank': True},
        }

    def create(self, validated_data):
        if not validated_data.get("company_name") or not validated_data.get("company_url"):
            raise serializers.ValidationError("Both company_name and company_url must be provided for new companies.")
        company = CompanyProfile.objects.create(**validated_data)
        company.current_employees.add(self.context["request"].user)
        return company
