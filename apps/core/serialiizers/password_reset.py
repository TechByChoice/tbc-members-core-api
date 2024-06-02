from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework import serializers

from apps.core.models import CustomUser


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = CustomUser.objects.get(email=value)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        uidb64 = self.context['uidb64']
        token = self.context['token']
        uid = force_str(urlsafe_base64_decode(uidb64))
        try:
            user = CustomUser.objects.get(pk=uid)
        except CustomUser.DoesNotExist:
            print('no account for password reset')
            raise serializers.ValidationError("Invalid token or user ID")
        if not default_token_generator.check_token(user, token):
            print('Token is invalid')
            raise serializers.ValidationError("Invalid token")
        user.set_password(data['password'])
        user.save()
        return data
