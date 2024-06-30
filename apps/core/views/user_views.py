# apps/core/user_views.py
import os

import requests
from knox.models import AuthToken
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework import status, viewsets
from django.db import transaction

from apps.company.models import CompanyProfile
from apps.core.serializers.user_serializers import CustomUserSerializer, RegisterSerializer, BaseUserSerializer
from apps.core.serializers.profile_serializers import UserProfileSerializer, UpdateProfileAccountDetailsSerializer
from apps.core.serializers.talent_serializers import TalentProfileSerializer
from apps.company.serializers import CompanyProfileSerializer
from apps.core.models import UserProfile
from apps.member.models import MemberProfile
from apps.mentorship.models import MentorshipProgramProfile, MentorProfile, MenteeProfile, MentorRoster
from apps.mentorship.serializer import MentorshipProgramProfileSerializer, MentorRosterSerializer
from utils.company_utils import create_or_update_company_connection
from utils.data_utils import extract_user_data, extract_company_data, extract_profile_data, extract_talent_data, \
    extract_profile_id_data
from utils.logging_helper import get_logger, log_exception, timed_function
from utils.cache_utils import cache_decorator
from utils.api_helpers import api_response
from utils.profile_utils import get_user_profile, update_user_profile
from utils.emails import send_dynamic_email
from utils.slack import fetch_new_posts, send_invite

logger = get_logger(__name__)


class UserDataView(APIView):
    permission_classes = [IsAuthenticated]

    @log_exception(logger)
    @timed_function(logger)
    @cache_decorator(timeout=300)  # Cache for 5 minutes
    def get(self, request):
        user = request.user
        try:
            user_profile = get_user_profile(user.id)
            user_data = CustomUserSerializer(user).data
            profile_data = UserProfileSerializer(user_profile).data

            response_data = {
                "user_info": {
                    **user_data,
                    "userprofile": profile_data,
                },
                "account_info": {field: getattr(user, field) for field in [
                    "is_staff", "is_recruiter", "is_member", "is_member_onboarding_complete",
                    "is_mentor", "is_mentee", "is_mentor_profile_active", "is_open_doors",
                    "is_open_doors_onboarding_complete", "is_mentor_profile_removed", "is_mentor_training_complete",
                    "is_mentor_interviewing", "is_mentor_profile_paused",
                    "is_community_recruiter", "is_company_account", "is_email_confirmation_sent",
                    "is_email_confirmed", "is_company_onboarding_complete",
                    "is_mentor_profile_approved", "is_mentor_application_submitted",
                    "is_speaker", "is_volunteer", "is_team", "is_community_recruiter",
                    "is_company_account", "is_partnership", "is_company_review_access_active"
                ]},
                "mentor_details": {},
                "mentee_details": {},
                "mentor_roster_data": {},
            }

            # Mentor application data
            if user.is_mentor_application_submitted:
                mentor_application = get_object_or_404(MentorshipProgramProfile, user=user)
                response_data["mentor_data"] = MentorshipProgramProfileSerializer(mentor_application).data

            # Mentee data
            if user.is_mentee:
                mentee_profile = get_object_or_404(MenteeProfile, user=user)
                response_data["mentee_details"] = {"id": mentee_profile.id}
                mentorship_roster = MentorRoster.objects.filter(mentee=mentee_profile)
                if mentorship_roster.exists():
                    response_data["mentor_roster_data"] = MentorRosterSerializer(mentorship_roster, many=True).data

            # Talent profile data
            member_profile = MemberProfile.objects.filter(user=user).first()
            if member_profile:
                response_data["user_info"]["memberprofile"] = TalentProfileSerializer(member_profile).data

            # Company account data
            if user.is_company_account:
                company_account_details = get_object_or_404(CompanyProfile, account_owner=user)
                local_company_data = CompanyProfileSerializer(company_account_details).data

                # External API call for additional company details
                company_id = company_account_details.id
                full_company_details_url = f'{os.environ.get("TC_API_URL")}core/api/company/details/?company_id={company_id}'
                try:
                    response = requests.get(full_company_details_url, timeout=5)
                    response.raise_for_status()
                    company_account_data = response.json()
                    company_account_data["company_profile"] = local_company_data
                except requests.RequestException as e:
                    logger.error(f"Error fetching company details: {str(e)}")
                    company_account_data = {"error": "Could not fetch company details"}

                response_data["company_account_data"] = company_account_data

            return api_response(data=response_data, message="User data retrieved successfully")

        except Exception as e:
            logger.error(f"Error retrieving user data for user {user.id}: {str(e)}")
            return api_response(message="An error occurred while retrieving user data", status_code=500)


class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @log_exception(logger)
    @timed_function(logger)
    def post(self, request):
        user = request.user
        serializer = UserProfileSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            updated_profile = update_user_profile(user.id, serializer.validated_data)
            return api_response(
                data=UserProfileSerializer(updated_profile).data,
                message="Profile updated successfully"
            )
        return api_response(errors=serializer.errors, status_code=400)


class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    @log_exception(logger)
    @timed_function(logger)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_member = True

            # Create the UserProfile and MemberProfile to replate the signal file
            UserProfile.objects.create(user=user)
            MemberProfile.objects.create(user=user)

            try:
                send_dynamic_email({
                    "recipient_emails": [user.email],
                    "template_id": "d-342822c240ed43778ba9e94a04fb10cf",
                    "dynamic_template_data": {
                        "first_name": user.first_name,
                    },
                })
                user.is_email_confirmation_sent = True
            except Exception as e:
                user.is_email_confirmation_sent = False
                logger.error(f"Failed to send welcome email: {str(e)}")
            _, token = AuthToken.objects.create(user)
            user.save()
            return api_response(message="User created successfully", data={"token": token},
                                status_code=status.HTTP_201_CREATED)
        return api_response(errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


# TODO | REFACTOR => MOVE TO apps.company
class CompanyRegistrationView(APIView):
    permission_classes = [AllowAny]

    @log_exception(logger)
    @timed_function(logger)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                user = serializer.save()
                company_profile = CompanyProfile.objects.create(
                    account_creator=user,
                    company_name=request.data.get('company_name')
                )
                company_profile.account_owner.add(user)
                company_profile.hiring_team.add(user)

                try:
                    send_dynamic_email({
                        "recipient_emails": [user.email],
                        "template_id": "your_welcome_email_template_id",
                        "dynamic_template_data": {
                            "first_name": user.first_name,
                            "company_name": company_profile.company_name,
                        },
                    })
                except Exception as e:
                    logger.error(f"Failed to send welcome email: {str(e)}")

            return api_response(message="Company and user created successfully", status_code=status.HTTP_201_CREATED)
        return api_response(errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class UserProfileManagementView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @log_exception(logger)
    @timed_function(logger)
    @action(detail=False, methods=['POST'])
    def update_notifications(self, request):
        user_profile = request.user.userprofile
        fields_to_update = [
            "marketing_jobs", "marketing_events", "marketing_org_updates",
            "marketing_identity_based_programing", "marketing_monthly_newsletter"
        ]
        for field in fields_to_update:
            setattr(user_profile, field, bool(request.data.get(field)))
        user_profile.save()
        return api_response(message="Notification preferences updated successfully")

    @log_exception(logger)
    @timed_function(logger)
    @action(detail=False, methods=['POST'])
    def update_identity(self, request):
        user_profile = request.user.userprofile
        serializer = UserProfileSerializer(user_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(message="Identity information updated successfully")
        return api_response(errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    @log_exception(logger)
    @timed_function(logger)
    @action(detail=False, methods=['POST'])
    def update_social_accounts(self, request):
        user_profile = request.user.userprofile
        serializer = UserProfileSerializer(user_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(message="Social accounts updated successfully")
        return api_response(errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    @log_exception(logger)
    @timed_function(logger)
    @action(detail=False, methods=['POST'])
    def update_skills_roles(self, request):
        user_profile = request.user.memberprofile
        serializer = TalentProfileSerializer(user_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(message="Skills and roles updated successfully")
        return api_response(errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    @log_exception(logger)
    @timed_function(logger)
    @action(detail=False, methods=['POST'])
    def update_work_place(self, request):
        user = request.user
        company_data = request.data.get("select_company")
        if company_data:
            company = CompanyProfile.objects.get(id=company_data["id"])
        else:
            company_serializer = CompanyProfileSerializer(data=request.data, context={"request": request})
            if company_serializer.is_valid():
                company = company_serializer.save()
            else:
                return api_response(errors=company_serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        company.current_employees.add(user)

        user_profile = user.memberprofile
        serializer = TalentProfileSerializer(user_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(message="Work place information updated successfully")
        return api_response(errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    @log_exception(logger)
    @timed_function(logger)
    @action(detail=False, methods=['POST'])
    def update_account_details(self, request):
        user = request.user
        try:
            profile = user.userprofile
        except UserProfile.DoesNotExist:
            return api_response(message="Profile not found", status_code=status.HTTP_404_NOT_FOUND)

        serializer = UpdateProfileAccountDetailsSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(message="Account details updated successfully")
        return api_response(errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


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
            profile_data = extract_profile_id_data(data, request.FILES)
            talent_data = extract_profile_id_data(data, request.FILES)

            with transaction.atomic():
                # Update user
                user_serializer = CustomUserSerializer(request.user, data=user_data, partial=True)
                user_serializer.is_valid(raise_exception=True)
                user = user_serializer.save()

                # Update talent profile
                talent_serializer = TalentProfileSerializer(user.user, data=talent_data, partial=True)
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@log_exception(logger)
@timed_function(logger)
def get_announcement(request):
    try:
        slack_msg = fetch_new_posts("CELK4L5FW", 1)
        if slack_msg:
            return api_response(data={"announcement": slack_msg}, message="Announcement retrieved successfully")
        else:
            return api_response(message="No new messages.", status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error pulling slack message: {str(e)}")
        return api_response(message="An error occurred while fetching the announcement",
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
