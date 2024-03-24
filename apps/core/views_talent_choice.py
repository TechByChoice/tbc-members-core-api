import requests
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import viewsets, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from rest_framework.decorators import action

from utils.helper import prepend_https_if_not_empty
from .models import CustomUser
from ..company.models import CompanyProfile


class CompanyViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['post'], url_path='service-agreement')
    def service_agreement(self, request):
        if request.data.get('confirm_service_agreement'):
            user = request.user
            company_profile = CompanyProfile.objects.get(account_creator=user)
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

    @action(detail=False, methods=['get'], url_path='confirm-email/(?P<id>[^/]+)/(?P<token>[^/]+)')
    def confirm_account_email(self, request, id=None, token=None):
        try:
            uid = force_str(urlsafe_base64_decode(id))
            user = get_object_or_404(CustomUser, id=uid)
            if default_token_generator.check_token(user, token):
                user.is_active = True
                user.is_email_confirmed = True

                user.save()
                return Response({
                    "status": True,
                    "token": token,
                    "message": "Email confirmed! Please complete your account."
                }, status=status.HTTP_200_OK)
            else:
                return Response({"status": False, "message": "Invalid email token."},
                                status=status.HTTP_400_BAD_REQUEST)

        except CustomUser.DoesNotExist as e:
            print(f"Can't find user Error: {e}")

        # except jwt.DecodeError:
        #     return Response({"status": False, "error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
