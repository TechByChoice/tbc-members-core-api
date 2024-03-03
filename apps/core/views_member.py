from django.core.serializers import serialize
from django.http import Http404
from rest_framework import status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.company.models import CompanyProfile
from apps.core.models import CustomUser, UserProfile
from apps.core.serializers import TalentProfileSerializer
from apps.core.serializers_member import CustomUserSerializer, UserProfileSerializer
from apps.core.util import get_current_company_data
from apps.mentorship.models import (
    MentorProfile,
    MenteeProfile,
    MentorshipProgramProfile,
)
from apps.mentorship.serializer import (
    MentorProfileSerializer,
    MenteeProfileSerializer,
    MentorshipProgramProfileSerializer,
)
from apps.member.models import MemberProfile


class MemberDetailsView(APIView):
    """
    Retrieve CustomUser, UserProfile, and MemberProfile details.
    """

    permission_classes = [IsAuthenticated]

    #     # @permission_classes([IsAuthenticated])
    def get_profile(self, model, user):
        try:
            return model.objects.get(user=user)
        except model.DoesNotExist:
            return None

    # @permission_classes([IsAuthenticated])
    def get(self, request, pk, format=None):
        try:
            user = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            raise Http404("Member not found.")

        user_profile = self.get_profile(UserProfile, user)
        if not user_profile:
            raise Http404("User profile not found.")

        talent_profile = self.get_profile(MemberProfile, user)
        if not talent_profile:
            raise Http404("Talent profile not found.")

        mentor_program = self.get_profile(MentorshipProgramProfile, user)
        current_company_data = get_current_company_data(user)

        user_serializer = CustomUserSerializer(user)
        user_profile_serializer = UserProfileSerializer(user_profile)
        talent_profile_serializer = TalentProfileSerializer(talent_profile)
        mentor_program_serializer = None
        if mentor_program and user.is_mentor_profile_active:
            mentor_program_serializer = MentorshipProgramProfileSerializer(
                mentor_program
            )

        data = {
            "user": user_serializer.data,
            "user_profile": user_profile_serializer.data,
            "talent_profile": talent_profile_serializer.data,
            "current_company": current_company_data,
            "mentorship_program": mentor_program_serializer.data
            if mentor_program_serializer
            else None,
        }

        return Response(
            {
                "success": True,
                "message": "Member details retrieved successfully.",
                "data": data,
            },
            status=status.HTTP_200_OK,
        )
