# apps/core/user_views.py
from knox.models import AuthToken
from rest_framework.decorators import api_view, permission_classes, action
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
from apps.mentorship.models import MentorshipProgramProfile, MentorProfile
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
        user_profile = get_user_profile(user.id)
        user_data = CustomUserSerializer(user).data
        profile_data = BaseUserSerializer(user).data
        response_data = {
            "user_info": user_data,
            "account_info": profile_data,
        }
        return api_response(data=response_data, message="User data retrieved successfully")


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
