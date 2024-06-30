from rest_framework import serializers
from apps.core.models import CommunityNeeds


class CommunityNeedsSerializer(serializers.ModelSerializer):
    """
    Serializer for CommunityNeeds model.
    """

    class Meta:
        model = CommunityNeeds
        fields = '__all__'


class GenericBreakdownSerializer(serializers.Serializer):
    """
    Generic serializer for breakdown data.
    """
    name = serializers.CharField(read_only=True)
    user_count = serializers.IntegerField()
