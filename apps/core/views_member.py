from django.core.serializers import serialize
from django.http import Http404
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
    def get_profile(self, model, user):
        try:
            return model.objects.get(user=user)
        except model.DoesNotExist:
            return None

    def get_current_company_data(self, user):
        try:
            company = CompanyProfile.objects.get(current_employees=user)
            return {
                "id": company.id,
                "company_name": company.company_name,
                "logo": company.logo.url,
                "company_size": company.company_size,
                "industries": [industry.name for industry in company.industries.all()]
            }
        except CompanyProfile.DoesNotExist:
            return None

    def get(self, request, pk, format=None):
        try:
            user = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            raise Http404('Member not found.')

        user_profile = self.get_profile(UserProfile, user)
        if not user_profile:
            raise Http404('User profile not found.')

        talent_profile = self.get_profile(TalentProfile, user)
        if not talent_profile:
            raise Http404('Talent profile not found.')

        mentor_program = self.get_profile(MentorshipProgramProfile, user)
        current_company_data = self.get_current_company_data(user)

        user_serializer = CustomUserSerializer(user)
        user_profile_serializer = UserProfileSerializer(user_profile)
        talent_profile_serializer = TalentProfileSerializer(talent_profile)
        mentor_program_serializer = None
        if mentor_program and user.is_mentor_profile_active:
            mentor_program_serializer = MentorshipProgramProfileSerializer(mentor_program)

        data = {
            'user': user_serializer.data,
            'user_profile': user_profile_serializer.data,
            'talent_profile': talent_profile_serializer.data,
            'current_company': current_company_data,
            'mentorship_program': mentor_program_serializer.data if mentor_program_serializer else None
        }

        return Response({
            'success': True,
            'message': 'Member details retrieved successfully.',
            'data': data
        }, status=status.HTTP_200_OK)
