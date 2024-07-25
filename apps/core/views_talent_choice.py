import json
import logging
import os

import requests
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import csrf_exempt
from knox.models import AuthToken
from rest_framework import viewsets, status
from rest_framework.generics import get_object_or_404
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from utils.helper import prepend_https_if_not_empty
from utils.slack import post_message
from .models import CustomUser
from ..company.models import CompanyProfile

logger = logging.getLogger(__name__)


class CompanyViewSet(ViewSet):

    @action(detail=True, methods=['post'], url_path='complete-onboarding')
    def complete_onboarding(self, request):
            company_profile = CompanyProfile.objects.get(account_creator=request.user)
            company_id = company_profile.id
        
            user_data = request.user
    
            # Prepare the data to include the token
            data_to_send = request.data.copy()
            if request.auth:
                data_to_send['token'] = str(request.auth)
                data_to_send['companyId'] = company_id
    
            try:
                response = requests.post(
                    f'{os.environ["TC_API_URL"]}company/new/onboarding/open-roles/',
                    data=json.dumps(data_to_send),
                    headers={'Content-Type': 'application/json'},
                    verify=True
                )
                response.raise_for_status()
                talent_choice_jobs = response.json()
            except requests.exceptions.HTTPError as http_err:
                return Response(
                    {"status": False, "error": f"HTTP error occurred: {http_err}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
            # Update user data to indicate onboarding completion
            user_data.is_company_onboarding_complete = True
            user_data.save()
            msg = (
                f":new: *New Talent Choice Onboarding Complete* :new:\n\n"
                f"*Company Name* {company_profile.company_name}\n\n"
                f"*Contact* {user_data.first_name}\n\n"
            )
            post_message("GL4BCC2HK", msg)
    
            return Response({
                "status": True,
                "message": "Welcome to Talent Choice."
            }, status=status.HTTP_200_OK)

    @csrf_exempt
    @action(detail=False, methods=['post'], url_path='service-agreement')
    def service_agreement(self, request):
        if request.data.get('confirm_service_agreement'):
            user = request.user
            company_profile = CompanyProfile.objects.get(account_creator=user)
            token = request.headers.get('Authorization', None)
            if token:
                clean_token = token.split()[1]
            else:
                clean_token = request.auth
            print(clean_token)

            try:
                response = requests.post(f'{os.environ["TC_API_URL"]}company/new/onboarding/confirm-terms/',
                                         data={'companyId': company_profile.id, 'token': clean_token}, verify=True)
                response.raise_for_status()
                talent_choice_jobs = response.json()
            except requests.exceptions.HTTPError as http_err:
                return Response(
                    {"status": False, "error": f"HTTP error occurred: {http_err}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            company_profile.confirm_service_agreement = True
            company_profile.save()

            return Response({
                "status": True,
                "message": "Welcome to Talent Choice."
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": False,
                "message": "Please accept the service agreement to create your account."
            }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='create-onboarding')
    def create_onboarding(self, request):
        if request.data:
            user = request.user
            company_profile = CompanyProfile.objects.get(account_creator=user)

            # Access form fields
            company_url = prepend_https_if_not_empty(request.data.get('website', ''))
            linkedin = prepend_https_if_not_empty(request.data.get('linkedin', ''))
            twitter = prepend_https_if_not_empty(request.data.get('twitter', ''))
            youtube = prepend_https_if_not_empty(request.data.get('youtube', ''))
            facebook = prepend_https_if_not_empty(request.data.get('facebook', ''))
            instagram = prepend_https_if_not_empty(request.data.get('instagram', ''))

            location = request.data.get('location', '')
            city = request.data.get('city', '')
            state = request.data.get('state', '')
            postal_code = request.data.get('postalCode', '')
            mission = request.data.get('mission')
            # For single value fields like autocomplete where the value is expected as a string
            company_size = request.data.get('company_size')
            # company_types = request.data.get('company_types')

            # For the file upload, the 'logo' field should be a file type
            logo = request.FILES.get('logo')
            if logo:
                company_profile.logo = logo

            company_profile.company_url = company_url
            company_profile.linkedin = linkedin
            company_profile.twitter = twitter
            company_profile.youtube = youtube
            company_profile.facebook = facebook
            company_profile.instagram = instagram
            company_profile.location = location
            company_profile.state = state
            company_profile.city = city
            company_profile.postal_code = postal_code
            company_profile.mission = mission
            company_profile.company_size = company_size
            # company_profile.company_types.set(company_types)
            # company_profile.industries.set(request.data.get('company_industries'))
            company_profile.save()
            return Response({'status': True, "companyId": company_profile.id}, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "status": False,
                "message": "Issue saving account data",
            }, status=status.HTTP_400_BAD_REQUEST)


class ConfirmEmailAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, id=None, token=None):
        print("starting email confirmation flow")
        try:
            # Decode the user ID
            uid = force_str(urlsafe_base64_decode(id))
            user = get_object_or_404(CustomUser, id=uid)

            if user.is_email_confirmed:
                return Response({
                    "status": True,
                    "message": "Email already confirmed!"
                }, status=status.HTTP_208_ALREADY_REPORTED)
            # Validate the token
            is_token_valid = default_token_generator.check_token(user, token)

            if is_token_valid:

                # Confirm the email
                user.is_active = True
                user.is_email_confirmed = True
                user.save()

                _, token = AuthToken.objects.create(user)

                return Response({
                    "status": True,
                    "token": token,
                    "message": "Email confirmed! Please complete your account."
                }, status=status.HTTP_200_OK)
            else:
                return Response({"status": False, "message": "Invalid email token. Please contact support."},
                                status=status.HTTP_400_BAD_REQUEST)

        except CustomUser.DoesNotExist:
            logger.warning(f"User does not exist for id: {id}")
            return Response({"status": False, "message": "Invalid email token or user does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unhandled error: {e}")
            return Response({"status": False, "message": "An unexpected error occurred."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # except jwt.DecodeError:
        #     return Response({"status": False, "error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
