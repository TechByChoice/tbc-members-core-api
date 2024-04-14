from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.core.exceptions import ValidationError

# Assuming your CustomUser model is the default user model
User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=False)  # Make first_name optional
    last_name = serializers.CharField(required=False)  # Make last_name optional

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password']
        extra_kwargs = {
            'first_name': {'required': False},  # Explicitly marking as optional
            'last_name': {'required': False},
        }

    def validate_email(self, value):
        """
        Check that the email provided is valid and not already in use.
        """
        User = get_user_model()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        """
        Create and return a new user, utilizing the custom user manager.
        """
        email = validated_data['email']
        password = validated_data['password']
        first_name = validated_data.get('first_name', '')
        last_name = validated_data.get('last_name', '')

        # Using the create_user method from your custom user manager.
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Additional user setup can be done here if necessary

        return user
