import os

from django.contrib.auth import user_logged_out
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from knox.auth import TokenAuthentication
from knox.models import AuthToken
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.core.models import CustomUser
from apps.core.serialiizers.password_reset import SetNewPasswordSerializer, PasswordResetSerializer
from apps.core.serializers.user_serializers import UserAccountInfoSerializer, CustomAuthTokenSerializer, \
    BaseUserSerializer
from utils.api_helpers import api_response
from utils.emails import send_password_email
from utils.logging_helper import get_logger, log_exception, timed_function

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

        _, token = AuthToken.objects.create(user)

        user_serializer = BaseUserSerializer(user)
        account_info_serializer = UserAccountInfoSerializer(user)

        return api_response(
            data={
                "token": token,
                "user_info": user_serializer.data,
                "account_info": account_info_serializer.data,
            },
            message="Login successful"
        )


class LogoutView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @log_exception(logger)
    @timed_function(logger)
    def post(self, request):
        """
        Log out the user and delete the authentication token.
        """
        request._auth.delete()
        user_logged_out.send(
            sender=request.user.__class__, request=request, user=request.user
        )
        return api_response(message="Logout successful", status_code=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @log_exception(logger)
    @timed_function(logger)
    def post(self, request):
        """
        Send a password reset request to the user via email
        """
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
            send_password_email(user.email, user.first_name, user, reset_link)

            return api_response(message="Password reset link sent.")
        return api_response(errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @log_exception(logger)
    @timed_function(logger)
    def post(self, request, uidb64, token):
        """
        Update user password if token is valid
        """
        serializer = SetNewPasswordSerializer(data=request.data, context={'uidb64': uidb64, 'token': token})
        if serializer.is_valid():
            return api_response(message="Password has been reset.")
        return api_response(errors=serializer.errors, message="Error: We could not update your password.",
                            status_code=status.HTTP_400_BAD_REQUEST)
