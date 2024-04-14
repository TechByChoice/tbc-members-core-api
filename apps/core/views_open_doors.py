import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from knox.models import AuthToken
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.core.mail import send_mail
from django.urls import reverse
import uuid

from rest_framework.viewsets import ViewSet

from .models import UserVerificationToken
from .serializers import UserProfileSerializer
from django.contrib.auth import get_user_model

from .serializers_open_doors import UserRegistrationSerializer
from .views import send_welcome_email

User = get_user_model()


class UserManagementView(ViewSet):

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


    def create(self, request, *args, **kwargs):
        """
        Create a new Open Doors user. This view handles the POST request to register a new user.
        It performs input validation, user creation, and sending a welcome email.
        """
        if request.method != "POST":
            return JsonResponse(
                {"status": False, "error": "Invalid request method"}, status=405
            )
        # This assumes the action is for registration.
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_open_doors = True
            user.save()
            _, token = AuthToken.objects.create(user)
            verification_token = str(uuid.uuid4())
            UserVerificationToken.objects.create(user=user, token=verification_token)
            frontend_url = os.getenv("FRONTEND_URL", "default_fallback_url")
            verification_url = f"{frontend_url}?token={verification_token}"
            send_welcome_email(user.email, user.first_name, company_name='reviewSite', user=user, current_site=frontend_url, request=request)
            return Response({'status': True,
                             "token": token,
                             'message': 'User registered. Please check your email.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='confirm-agreement')
    def service_agreement(self, request):
        if request.data.get('confirm_service_agreement'):
            user = request.user
            user.confirm_service_agreement = True
            user.is_open_doors_onboarding_complete = True
            user.is_company_review_access_active = True
            user.save()

            return Response({
                "status": True,
                "message": "Welcome to Open Doors."
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": False,
                "message": "Please accept the service agreement to create your account."
            }, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        # This assumes the action is for updating user demographics.
        user = request.user  # Assuming the user is authenticated
        serializer = UserProfileSerializer(user.userprofile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User profile updated successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
