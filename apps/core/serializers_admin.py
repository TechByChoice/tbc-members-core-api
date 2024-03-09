from rest_framework import serializers


class GenericBreakdownSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)  # Assuming each model has a name field
    user_count = serializers.IntegerField()
