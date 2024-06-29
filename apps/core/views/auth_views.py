import os
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.core.models import CustomUser
from apps.core.serialiizers.password_reset import SetNewPasswordSerializer, PasswordResetSerializer
from apps.core.serializers.user_serializers import CustomAuthTokenSerializer
from utils.logging_helper import get_logger, log_exception, timed_function
from utils.emails import send_dynamic_email
from utils.api_helpers import api_response

logger = get_logger(__name__)


class UserPermissionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @log_exception(logger)
    @timed_function(logger)
    def get(self, request):
        permissions = request.user.is_authenticated
        return api_response(data={'permissions': permissions}, message="User permissions retrieved")


class LoginView(APIView):
    permission_classes = [AllowAny]

    @log_exception(logger)
    @timed_function(logger)
    def post(self, request):
        serializer = CustomAuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = user.auth_token.key
        return api_response(
            data={
                "token": token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                }
            },
            message="Login successful"
        )


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @log_exception(logger)
    @timed_function(logger)
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            user = CustomUser.objects.get(email=serializer.validated_data['email'])
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"{os.getenv('FRONTEND_URL')}password-reset/confirm-password/{uidb64}/{token}"

            email_data = {
                "recipient_emails": [user.email],
                "template_id": "your_password_reset_template_id",
                "dynamic_template_data": {
                    "username": user.first_name,
                    "reset_link": reset_link,
                },
            }
            send_dynamic_email(email_data)

            return api_response(message="Password reset link sent.")
        return api_response(errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @log_exception(logger)
    @timed_function(logger)
    def post(self, request, uidb64, token):
        serializer = SetNewPasswordSerializer(data=request.data, context={'uidb64': uidb64, 'token': token})
        if serializer.is_valid():
            return api_response(message="Password has been reset.")
        return api_response(errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
