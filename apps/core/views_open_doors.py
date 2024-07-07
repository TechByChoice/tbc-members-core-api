import os

import requests
from django.http import JsonResponse
from knox.models import AuthToken
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
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
from ..company.models import CompanyProfile

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
            user.is_company_review_access_active = True
            user.save()
            _, token = AuthToken.objects.create(user)
            verification_token = str(uuid.uuid4())
            UserVerificationToken.objects.create(user=user, token=verification_token)
            frontend_url = os.getenv("FRONTEND_URL", "default_fallback_url")
            verification_url = f"{frontend_url}?token={verification_token}"
            send_welcome_email(user.email, user.first_name, company_name='reviewSite', user=user,
                               current_site=frontend_url, request=request)
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

    @action(detail=False, methods=['post'], url_path='submit-report')
    def post_review_submission(self, request):
        """
        Sends item ID and form data to a 3rd party API.

        :param request: The request object containing form data.
        :param pk: Primary key of the item to be processed, taken from the URL.
        :return: A Response object with the result of the 3rd party API interaction.
        """
        user_id = request.user.id
        # Create a mutable copy of request.data
        header_token = request.headers.get("Authorization", None)
        mutable_data = request.data.copy()
        mutable_data['user_id'] = user_id
        mutable_data['header_token'] = header_token

        # create new company
        if mutable_data.get('company_name') and mutable_data['company_url']:
            print(mutable_data.get('company_name'))
            new_company = CompanyProfile.objects.create(company_name=mutable_data.get('company_name'), company_url=mutable_data.get('company_url'))
            mutable_data['company_id'] = new_company.id
            print(f'Created a new company: {new_company.company_name} ID: {new_company.id}')

        third_party_url = f'{os.getenv("OD_API_URL")}reports/submit-report/'

        # Make the 3rd party API request
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": header_token
            }
            response = requests.post(third_party_url, json=mutable_data, headers=headers)
            response.raise_for_status()
            # Process the response from the 3rd party API
            result_data = response.json()
            print("Successfully submitted data to OD: submit-report")
            return Response(result_data, status=status.HTTP_200_OK)
        except requests.RequestException as e:
            print(f"Exception occurred will calling OD: submit-report: {e}")
            return Response({"status": False, "message": "No data saved"})

    @action(detail=True, methods=['get'], url_path='get-report')
    def get_review_submission(self, request, pk=None):
        """
        Submits the the review

        :param request: The request object containing form data.
        :param pk: Primary key of the item to be processed, taken from the URL.
        :return: A Response object with the result of the 3rd party API interaction.
        """
        user_id = request.user.id
        # # Create a mutable copy of request.data
        header_token = request.headers.get("Authorization", None)
        data = {"id": user_id}
        # mutable_data['user_id'] = user_id
        # mutable_data['header_token'] = header_token
        third_party_url = f'{os.getenv("OD_API_URL")}reports/get/report/{pk}/'
        #
        # # Make the 3rd party API request
        try:
            response = requests.get(third_party_url, data=data)
            response.raise_for_status()
            # Process the response from the 3rd party API
            result_data = response.json()
            return Response(result_data, status=status.HTTP_200_OK)
        except requests.RequestException as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        #
        # return Response(data={"status": True}, status=status.HTTP_201_CREATED)
        return Response({"message": "Here is the report for ID: {}".format(pk)})
