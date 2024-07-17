import os

from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import permissions, views, response, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import CustomUser
from apps.core.serialiizers.password_reset import PasswordResetSerializer, SetNewPasswordSerializer


class UserPermissionAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        permissions = request.user.is_authenticated
        return response.Response({'permissions': permissions})


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = CustomUser.objects.get(email=serializer.validated_data['email'])
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"{os.getenv('FRONTEND_URL')}password-reset/confirm-password/{uidb64}/{token}"
            email_data = {
                'username': user.first_name,
                'reset_link': reset_link
            }

            send_password_email(user.email, user.first_name, user, reset_link)

            return Response({"status": True, "message": "Password reset link sent."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    serializer_class = SetNewPasswordSerializer

    def post(self, request, uidb64, token):
        serializer = self.serializer_class(data=request.data, context={'uidb64': uidb64, 'token': token})
        t = serializer.is_valid()
        print(t)
        if serializer.is_valid():
            return Response({"status": True, "message": "Password has been reset."}, status=status.HTTP_200_OK)
        return Response({"status": False, "message": "Token not valid"}, status=status.HTTP_400_BAD_REQUEST)


def send_password_email(email, first_name, user, reset_link):
    """
    Send a password reset email to the user.
    """
    mail_subject = 'Password Reset Request'

    context = {
        'username': first_name,
        'reset_link': reset_link,
    }

    message = render_to_string('emails/password_reset_email.txt', context=context)
    email_msg = EmailMessage(mail_subject, message, 'no-reply@yourdomain.com', [email])
    email_msg.extra_headers = {
        'email_template': 'emails/password_reset_email.html',
        'username': first_name,
        'reset_link': reset_link,
    }

    try:
        email_msg.send()
    except Exception as e:
        print("Error while sending email: ", str(e))

