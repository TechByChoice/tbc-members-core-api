from django.core.serializers import serialize
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.company.models import CompanyProfile
from apps.core.models import CustomUser, UserProfile
from apps.core.serializers import TalentProfileSerializer
from apps.core.serializers_member import CustomUserSerializer, UserProfileSerializer
from apps.mentorship.models import MentorProfile, MenteeProfile, MentorshipProgramProfile
from apps.mentorship.serializer import MentorProfileSerializer, MenteeProfileSerializer, \
    MentorshipProgramProfileSerializer
from apps.talent.models import TalentProfile


class MemberDetailsView(APIView):
    """
    Retrieve CustomUser, UserProfile, and TalentProfile details.
    """

    def get(self, request, pk, format=None):
        try:
            user = CustomUser.objects.get(pk=pk)
            user_profile = UserProfile.objects.get(user=user)
            talent_profile = TalentProfile.objects.get(user=user)

            try:
                mentor_program = MentorshipProgramProfile.objects.get(user=user.pk)
            except CompanyProfile.DoesNotExist:
                mentor_program = None

            try:
                current_company = CompanyProfile.objects.get(current_employees=user)
                current_company_data = {
                    "id": current_company.id,
                    "company_name": current_company.company_name,
                    "logo": current_company.logo.url,
                    "company_size": current_company.company_size,
                    "industries": [industry.name for industry in current_company.industries.all()]
                }
            except CompanyProfile.DoesNotExist:
                current_company = None
                current_company_data = None

            user_serializer = CustomUserSerializer(user)
            user_profile_serializer = UserProfileSerializer(user_profile)
            talent_profile_serializer = TalentProfileSerializer(talent_profile)

            if mentor_program:
                mentor_program_serializer = MentorshipProgramProfileSerializer(mentor_program)
            else:
                mentor_program_serializer = mentor_program

            data = {
                'user': user_serializer.data,
                'user_profile': user_profile_serializer.data,
                'talent_profile': talent_profile_serializer.data,
                'current_company': current_company_data,
                'mentorship_program': mentor_program_serializer.data
            }

            return Response({
                'success': True,
                'message': 'Member details retrieved successfully.',
                'data': data
            }, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Member not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User profile not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        except TalentProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Talent profile not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
