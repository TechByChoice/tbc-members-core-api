import os
import requests
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from knox.models import AuthToken
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.core.models import CustomUser, UserVerificationToken
from apps.core.serializers.user_serializers import UserRegistrationSerializer
from apps.core.serializers.profile_serializers import UserProfileSerializer
from utils.logging_helper import get_logger, log_exception, timed_function
from utils.emails import send_dynamic_email
from utils.api_helpers import api_response

logger = get_logger(__name__)


class UserManagementView(ViewSet):
    @log_exception(logger)
    @timed_function(logger)
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @log_exception(logger)
    @timed_function(logger)
    def create(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_open_doors = True
            user.is_company_review_access_active = True
            user.save()
            _, token = AuthToken.objects.create(user)
            verification_token = UserVerificationToken.create_token(user)
            frontend_url = os.getenv("FRONTEND_URL", "default_fallback_url")
            verification_url = f"{frontend_url}?token={verification_token.token}"

            email_data = {
                "recipient_emails": [user.email],
                "template_id": "your_welcome_email_template_id",
                "dynamic_template_data": {
                    "first_name": user.first_name,
                    "verification_url": verification_url,
                },
            }
            send_dynamic_email(email_data)

            return api_response(
                data={"token": token},
                message="User registered. Please check your email.",
                status_code=status.HTTP_201_CREATED
            )
        return api_response(errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='confirm-agreement')
    @log_exception(logger)
    @timed_function(logger)
    def service_agreement(self, request):
        if request.data.get('confirm_service_agreement'):
            user = request.user
            user.confirm_service_agreement = True
            user.is_open_doors_onboarding_complete = True
            user.is_company_review_access_active = True
            user.save()
            return api_response(message="Welcome to Open Doors.")
        else:
            return api_response(
                message="Please accept the service agreement to create your account.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @log_exception(logger)
    @timed_function(logger)
    def partial_update(self, request):
        user = request.user
        serializer = UserProfileSerializer(user.userprofile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(message="User profile updated successfully.")
        return api_response(errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='submit-report')
    @log_exception(logger)
    @timed_function(logger)
    def post_review_submission(self, request):
        user_id = request.user.id
        header_token = request.headers.get("Authorization", None)
        mutable_data = request.data.copy()
        mutable_data['user_id'] = user_id
        mutable_data['header_token'] = header_token
        third_party_url = f'{os.getenv("OD_API_URL")}reports/submit-report/'

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": header_token
            }
            response = requests.post(third_party_url, json=mutable_data, headers=headers)
            response.raise_for_status()
            return api_response(data=response.json(), message="Report submitted successfully")
        except requests.RequestException as e:
            logger.error(f"Error submitting report: {str(e)}")
            return api_response(message="Failed to submit report", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='get-report')
    @log_exception(logger)
    @timed_function(logger)
    def get_review_submission(self, request, pk=None):
        user_id = request.user.id
        data = {"id": user_id}
        third_party_url = f'{os.getenv("OD_API_URL")}reports/get/report/{pk}/'

        try:
            response = requests.get(third_party_url, data=data)
            response.raise_for_status()
            return api_response(data=response.json(), message="Report retrieved successfully")
        except requests.RequestException as e:
            logger.error(f"Error retrieving report: {str(e)}")
            return api_response(message="Failed to retrieve report", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
