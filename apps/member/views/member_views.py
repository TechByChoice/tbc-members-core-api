import logging
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db import transaction

from apps.core.models import CustomUser
from apps.core.serializers.user_serializers import CustomUserSerializer
from apps.core.serializers.profile_serializers import UserProfileSerializer
from apps.core.serializers.talent_serializers import TalentProfileSerializer
from apps.mentorship.models import MentorshipProgramProfile, MentorProfile
from utils.logging_helper import get_logger, log_exception, timed_function
from utils.data_utils import extract_user_data, extract_company_data, extract_profile_data, extract_talent_data
from utils.profile_utils import update_user_profile, update_talent_profile
from utils.company_utils import create_or_update_company_connection
from utils.emails import send_dynamic_email
from utils.slack import send_invite
from utils.api_helpers import api_response

logger = get_logger(__name__)


class MemberCreationView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]

    @log_exception(logger)
    @timed_function(logger)
    def post(self, request):
        """
        Create a new member profile for an existing user.

        This view handles the creation of a new member profile, including associated
        user profile, talent profile, and company connection. It also handles mentorship
        program creation if applicable.

        Returns:
            Response: A JSON response indicating success or failure of the operation.

        Raises:
            ValidationError: If the data provided is invalid.
            IntegrityError: If there's a database integrity error.
        """
        if request.user.is_member_onboarding_complete:
            return api_response(
                message="Member has already been created for this user.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = request.data
            user_data = extract_user_data(data)
            company_data = extract_company_data(data)
            profile_data = extract_profile_data(data, request.FILES)
            talent_data = extract_talent_data(data, request.FILES)

            with transaction.atomic():
                # Update user
                user_serializer = CustomUserSerializer(request.user, data=user_data, partial=True)
                user_serializer.is_valid(raise_exception=True)
                user = user_serializer.save()

                # Update talent profile
                talent_serializer = TalentProfileSerializer(user.memberprofile, data=talent_data, partial=True)
                talent_serializer.is_valid(raise_exception=True)
                talent_profile = talent_serializer.save()

                # Update user profile
                profile_serializer = UserProfileSerializer(user.userprofile, data=profile_data, partial=True)
                profile_serializer.is_valid(raise_exception=True)
                user_profile = profile_serializer.save()

                # Create or update company connection
                user_company_connection = create_or_update_company_connection(user, company_data)

                # Handle mentorship program
                if user_data.get("is_mentee") or user_data.get("is_mentor"):
                    mentorship_program = MentorshipProgramProfile.objects.create(user=user)
                    user.is_mentee = user_data.get("is_mentee", False)
                    user.is_mentor = user_data.get("is_mentor", False)
                    if user_data.get("is_mentor"):
                        mentor_profile = MentorProfile.objects.create(user=user)
                        mentorship_program.mentor_profile = mentor_profile
                        mentorship_program.save()

                    # Send welcome email
                    email_data = {
                        "recipient_emails": [user.email],
                        "template_id": "d-96a6752bd6b74888aa1450ea30f33a06",
                        "dynamic_template_data": {"first_name": user.first_name},
                    }
                    send_dynamic_email(email_data)

                user.is_member_onboarding_complete = True
                user.is_company_review_access_active = True
                user.save()

                # Send Slack invite
                try:
                    send_invite(user.email)
                    user.is_slack_invite_sent = True
                    user.save()
                except Exception as e:
                    logger.error(f"Failed to send Slack invite for user {user.id}: {str(e)}")
                    user.is_slack_invite_sent = False
                    user.save()

            return api_response(
                message="User, MemberProfile, and UserProfile created successfully!",
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error creating new member: {str(e)}")
            return api_response(
                message="An error occurred while creating the member profile.",
                errors=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
