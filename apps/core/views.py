import json
import os

import requests
from django.contrib.auth import user_logged_out
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.db import transaction
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from knox.auth import AuthToken, TokenAuthentication
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    throttle_classes,
    parser_classes,
    permission_classes,
)
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from api import settings
from apps.company.models import Roles, CompanyProfile, Skill, Department
from apps.core.models import (
    UserProfile,
    EthicIdentities,
    GenderIdentities,
    SexualIdentities,
    CustomUser,
)
from apps.core.serializers import (
    UserProfileSerializer,
    CustomAuthTokenSerializer,
    UpdateProfileAccountDetailsSerializer,
    CompanyProfileSerializer,
    TalentProfileSerializer,
)
from apps.core.util import (
    extract_user_data,
    extract_company_data,
    extract_profile_data,
    extract_talent_data,
    update_user,
    update_talent_profile,
    update_user_profile,
    create_or_update_company_connection,
)
from apps.member.models import MemberProfile
from apps.mentorship.models import MentorshipProgramProfile, MentorRoster, MenteeProfile, MentorProfile
from apps.mentorship.serializer import (
    MentorRosterSerializer,
    MentorshipProgramProfileSerializer,
)
from utils.data_utils import get_or_create_normalized
from utils.emails import send_dynamic_email
from utils.helper import prepend_https_if_not_empty
from utils.logging_helper import get_logger
from utils.profile_utils import update_user_company_association
from utils.sendgrid_helper import add_user_to_portal_form
from utils.slack import fetch_new_posts, send_invite, post_message

logger = get_logger(__name__)

CACHE_TIMEOUT = getattr(settings, 'ANNOUNCEMENT_CACHE_TIMEOUT', 300)


class LoginThrottle(UserRateThrottle):
    rate = "5/min"


@api_view(["POST"])
@throttle_classes([LoginThrottle])
@permission_classes([AllowAny])
def login_api(request):
    serializer = CustomAuthTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
    # userprofile = UserProfile.objects.get(user=user.id)
    # userprofile_serializer = UserProfileSerializer(userprofile)
    # userprofile_json_data = userprofile_serializer.data
    # userprofile.timezone = request.data['timezone']
    # userprofile.save()
    # create a token to track login
    _, token = AuthToken.objects.create(user)

    response = JsonResponse(
        {
            "status": True,
            "user_info": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "userprofile": [],
                # 'userprofile': userprofile_json_data
            },
            "account_info": {
                "is_staff": user.is_staff,
                "is_recruiter": user.is_recruiter,
                "is_member": user.is_member,
                "is_mentor": user.is_mentor,
                "is_mentee": user.is_mentee,
                "is_speaker": user.is_speaker,
                "is_volunteer": user.is_volunteer,
                "is_mentor_profile_active": user.is_mentor_profile_active,
                "is_mentor_training_complete": user.is_mentor_training_complete,
                "is_mentor_profile_approved": user.is_mentor_profile_approved,
                "is_mentor_application_submitted": user.is_mentor_application_submitted,
                "is_talent_source_beta": user.is_talent_source_beta,
                "is_team": user.is_team,
                "is_community_recruiter": user.is_community_recruiter,
                "is_company_account": user.is_company_account,
                "is_partnership": user.is_partnership,
                "is_company_review_access_active": user.is_company_review_access_active,
            },
            "token": token,
        }
    )

    # Set secure cookie
    response.set_cookie(
        "auth_token", token, secure=False, httponly=True, domain=os.environ["FRONTEND_URL"]
    )  # httponly=True to prevent access by JavaScript

    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_data(request):
    """
    Retrieve comprehensive user data including profile, account info, and role-specific details.

    This endpoint fetches and returns detailed information about the authenticated user,
    including their profile, account status, and any role-specific data (e.g., mentor, mentee).

    Returns:
        Response: A JSON response containing user data, account info, and role-specific details.

    Raises:
        Http404: If required user profiles are not found.
    """
    print('getting users details for app')
    user = request.user
    # cache_key = f'user_data_{user.id}'
    # cached_data = cache.get(cache_key)
    #
    # if cached_data:
    #     print('returning cached data')
    #     return Response(cached_data)

    try:
        print('getting users profiles for app')
        user_data = _fetch_user_data(user)
        # cache.set(cache_key, user_data, timeout=settings.USER_DATA_CACHE_TIMEOUT)
        # print('saving users profiles for app as cache')
        return Response(user_data)
    except Exception as e:
        print(f"Error fetching user data for user {user.id}: {str(e)}")
        return Response({"error": "An error occurred while fetching user data"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _fetch_user_data(user):
    cache_key = f"user_data_{user.id}"
    cached_data = cache.get(cache_key)
    user_profile = UserProfile.objects.select_related('user').get(user=user)

    if cached_data is None:
        user_profile = UserProfile.objects.select_related('user').get(user=user)    

    response_data = {
        "status": True,
        "user_info": _get_user_info(user, user_profile),
        "account_info": _get_account_info(user),
        "mentor_details": {},
        "mentee_details": {},
        "mentor_roster_data": {},
    }

    _add_conditional_data(user, response_data)
    _add_company_account_data(user, response_data)

    # Cache the data for 1 hour (3600 seconds)
    cache.set(cache_key, response_data, 3600)
    return response_data

    return response_data


def _get_user_info(user, user_profile):
    user_info = {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "userprofile": UserProfileSerializer(user_profile).data,
    }

    talent_profile = MemberProfile.objects.filter(user=user).first()
    if talent_profile:
        user_info["talentprofile"] = TalentProfileSerializer(talent_profile).data

    current_company = CompanyProfile.objects.filter(current_employees=user).first()
    if current_company:
        user_info["current_company"] = {
            "id": current_company.id,
            "logo_url": current_company.logo_url,
            "company_name": current_company.company_name,
            "company_url": current_company.company_url
        }

    return user_info


def _get_account_info(user):
    account_fields = [
        "is_staff", "is_recruiter", "is_member", "is_member_onboarding_complete",
        "is_mentor", "is_mentee", "is_mentor_profile_active", "is_open_doors",
        "is_open_doors_onboarding_complete", "is_open_doors_profile_complete", "is_mentor_profile_removed",
        "is_mentor_training_complete", "is_mentor_interviewing", "is_mentor_profile_paused",
        "is_community_recruiter", "is_company_account", "is_email_confirmation_sent",
        "is_email_confirmed", "is_company_onboarding_complete",
        "is_mentor_profile_approved", "is_mentor_application_submitted",
        "is_speaker", "is_volunteer", "is_team", "is_community_recruiter",
        "is_company_account", "is_partnership", "is_company_review_access_active"
    ]
    return {field: getattr(user, field) for field in account_fields}


def _add_conditional_data(user, response_data):
    if user.is_mentor_application_submitted:
        mentor_application = MentorshipProgramProfile.objects.get(user=user)
        response_data["mentor_data"] = MentorshipProgramProfileSerializer(mentor_application).data

    if user.is_mentee:
        mentee_profile = MenteeProfile.objects.get(user=user)
        response_data["mentee_details"] = {"id": mentee_profile.id}
        mentorship_roster = MentorRoster.objects.filter(mentee=mentee_profile)
        if mentorship_roster.exists():
            response_data["mentor_roster_data"] = MentorRosterSerializer(mentorship_roster, many=True).data


def _add_company_account_data(user, response_data):
    if user.is_company_account:
        company_account_details = CompanyProfile.objects.get(account_owner=user)
        local_company_data = CompanyProfileSerializer(company_account_details).data

        company_id = company_account_details.id
        full_company_details_url = f'{os.getenv("TC_API_URL")}core/api/company/details/?company_id={company_id}'

        try:
            response = requests.get(full_company_details_url, timeout=os.getenv("API_TIMEOUT"))
            response.raise_for_status()
            company_account_data = response.json()
            company_account_data["company_profile"] = local_company_data
        except requests.RequestException as e:
            print(f"Error fetching company details for company {company_id}: {str(e)}")
            company_account_data = {"error": "Could not fetch company details"}

        response_data["company_account_data"] = company_account_data


def get_company_data(user_details):
    company = get_object_or_404(CompanyProfile, account_owner=user_details)
    return CompanyProfileSerializer(company).data


@api_view(["GET"])
def get_announcement(request):
    """
    Retrieve the latest announcement from Slack.

    This endpoint fetches the most recent post from a specified Slack channel,
    caches it for improved performance, and returns it as an announcement.

    Returns:
        Response: A JSON response containing the announcement or an error message.
    """
    try:
        # Try to get the cached announcement
        cached_announcement = cache.get('latest_announcement')
        if cached_announcement:
            logger.info("Serving cached announcement")
            return Response({"announcement": cached_announcement}, status=status.HTTP_200_OK)

        # If not in cache, fetch new posts
        slack_msg = fetch_new_posts("CELK4L5FW", 1)
        if slack_msg:
            # Cache the new announcement
            cache.set('latest_announcement', slack_msg, CACHE_TIMEOUT)
            logger.info("New announcement fetched and cached")
            return Response({"announcement": slack_msg}, status=status.HTTP_200_OK)
        else:
            logger.warning("No new Slack messages found")
            return Response(
                {"message": "No new messages."}, status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        logger.error(f"Error pulling Slack message: {str(e)}", exc_info=True)
        return Response(
            {"error": "An unexpected error occurred."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# @login_required
@parser_classes([MultiPartParser])
@api_view(["POST"])
def create_new_member(request):
    if request.user.is_member_onboarding_complete:
        return Response(
            {
                "status": False,
                "message": "Member has already been created for this user.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        data = request.data
        user_data = extract_user_data(data)
        company_data = extract_company_data(data)
        profile_data = extract_profile_data(data, request.FILES)
        talent_data = extract_talent_data(data, request.FILES)

        with transaction.atomic():
            user = update_user(request.user, user_data)
            talent_profile = update_talent_profile(user, talent_data)
            user_profile = update_user_profile(user, profile_data)
            user_company_connection = create_or_update_company_connection(
                user, company_data
            )

            if user_data["is_mentee"] or user_data["is_mentor"]:
                mentorship_program = MentorshipProgramProfile.objects.create(user=user)
                request.user.is_mentee = user_data["is_mentee"]
                request.user.is_mentor = user_data["is_mentor"]
                if user_data["is_mentor"]:
                    mentor_profile = MentorProfile.objects.create(user=request.user)
                    mentorship_program.mentor_profile = mentor_profile
                    mentorship_program.save()

                template_id = "d-96a6752bd6b74888aa1450ea30f33a06"
                dynamic_template_data = {"first_name": request.user.first_name}

                email_data = {
                    "subject": "Welcome to Our Platform",
                    "recipient_emails": [request.user.email],
                    "template_id": template_id,
                    "dynamic_template_data": dynamic_template_data,
                }
                send_dynamic_email(email_data)
            request.user.is_member_onboarding_complete = True
            request.user.is_company_review_access_active = True 
            request.user.last_modified = timezone.now()
            request.user.save()
            # send slack invite
            try:
                send_invite(user.email)
                request.user.is_slack_invite_sent = True
            except Exception as e:
                request.user.is_slack_invite_sent = False
                print(e)
            try:
                # add to mailing list
                convert_kit_details = {
                    'email': request.user.email,
                    'first_name': request.user.first_name,
                }
                add_user_to_portal_form(convert_kit_details)
                request.user.is_sendgrid_invite_sent = True
            except Exception as e:
                request.user.is_sendgrid_invite_sent = False
                print(e)

        request.user.save()

        msg = (
            f":new: *New TBC Member* :new:\n\n"
            f"*Name* {user.first_name} \n\n"
        )
        post_message("GL4BCC2HK", msg)
        
        # Invalidate the cache for this user
        cache_key = f"user_data_{user.id}"
        cache.delete(cache_key)        

        return Response(
            {
                "status": True,
                "message": "User, MemberProfile, and UserProfile created successfully!",
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        # Handle specific known exceptions
        return Response(
            {"status": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        # Handle unexpected exceptions
        print(e)
        return Response(
            {"status": False, "error": "An unexpected error occurred."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@parser_classes([MultiPartParser])
@api_view(["POST"])
def create_od_user_profile(request):
    if request.user.is_open_doors_profile_complete:
        return Response(
            {
                "status": False,
                "message": "Profile has already been created for this user.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        data = request.data
        user_data = extract_user_data(data)
        profile_data = extract_profile_data(data, request.FILES)
        talent_data = extract_talent_data(data, request.FILES)

        with transaction.atomic():
            user = update_user(request.user, user_data)
            user_profile = update_user_profile(user, profile_data, True)

            request.user.is_open_doors_profile_complete = True
            request.user.save()

        msg = (
            f":new: *New OD Member Profile created* :new:\n\n"
            f"*Name* {user.first_name} \n\n"
        )
        post_message("GL4BCC2HK", msg)

        return Response(
            {
                "status": True,
                "message": "User, MemberProfile, and UserProfile created successfully!",
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        # Handle specific known exceptions
        return Response(
            {"status": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        # Handle unexpected exceptions
        print(e)
        return Response(
            {"status": False, "error": "An unexpected error occurred."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def get_new_company_data(request):
    return Response(
        {
            "status": True,
            "data": [
                {
                    "step": "Marketing Related Questions",
                    "questions": [
                        {
                            "order": 0,
                            "label": "Communication Settings",
                            "key": None,
                            "helper_text": "The following questions will help us understand what email and updates you want form us.",
                            "type": "title",
                            "options": None,
                        },
                        {
                            "order": 1,
                            "label": "Please details your would like to receive marketing about",
                            "key": None,
                            "helper_text": None,
                            "type": "header",
                            "options": None,
                        },
                        {
                            "order": 2,
                            "label": "Our Monthly Newsletter",
                            "key": "marketing_monthly_newsletter",
                            "helper_text": None,
                            "type": "checkbox",
                            "options": None,
                        },
                        {
                            "order": 3,
                            "label": "Community Events",
                            "key": "marketing_events",
                            "helper_text": None,
                            "type": "checkbox",
                            "options": None,
                        },
                        {
                            "order": 4,
                            "label": "Interest Based Programing",
                            "key": "marketing_identity_based_programing",
                            "helper_text": None,
                            "type": "checkbox",
                            "options": None,
                        },
                        {
                            "order": 5,
                            "label": "Open Jobs & Job Hunting Tips",
                            "key": "marketing_jobs",
                            "helper_text": None,
                            "type": "checkbox",
                            "options": None,
                        },
                        {
                            "order": 5,
                            "label": "Community Updates",
                            "key": "marketing_org_updates",
                            "helper_text": None,
                            "type": "checkbox",
                            "options": None,
                        },
                    ],
                }
            ],
        }
    )


@api_view(["POST"])
def update_profile_account_details(request):
    """
    Update the account details associated with a user's profile.

    This view function handles a POST request to update various fields of a user's profile. It leverages
    Django Rest Framework's serializer for data validation and saving. If the profile associated with the
    user does not exist, it returns an appropriate response.

    Parameters:
    - request: The HttpRequest object containing the POST data and the logged-in user's information.

    Returns:
    - Response: A DRF Response object. If the update is successful, it returns a success status and message.
                If the profile does not exist, it returns a 404 Not Found status with an error message.
                If the provided data is invalid, it returns a 400 Bad Request status with error details.

    Raises:
    - MemberProfile.DoesNotExist: If the UserProfile associated with the user does not exist.
    """
    user = request.user
    try:
        profile = user.userprofile
    except MemberProfile.DoesNotExist:
        return Response(
            {"status": False, "message": "Profile not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "POST":
        serializer = UpdateProfileAccountDetailsSerializer(
            profile, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": True, "message": "Form Saved"}, status=status.HTTP_200_OK
            )
        return Response(
            {"status": False, "message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
def update_profile_work_place(request):
    user = request.user

    # Handling existing, new, or removal of company
    company_details = request.data.get("select_company")
    given_company = request.data.get("company")
    company = None

    if company_details or given_company:
        if company_details:
            try:
                company = CompanyProfile.objects.get(id=company_details["id"])
            except CompanyProfile.DoesNotExist:
                return Response(
                    {"status": False, "detail": "Company does not exist."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif request.data.get("company_name"):  # Handling new company
            company_serializer = CompanyProfileSerializer(
                data=request.data, context={"request": request}
            )
            if company_serializer.is_valid():
                company = company_serializer.save()
            else:
                return Response(
                    {"status": False, "message": company_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    # Update user's company association
    try:
        old_company, updated_company = update_user_company_association(user, company)
    except Exception as e:
        return Response(
            {"status": False, "detail": f"Error updating company association: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Updating talent profile
    talent_profile = get_object_or_404(MemberProfile, user=user)
    role_names = request.data.get("job_roles", [])

    roles_to_set = []
    for role_name in role_names:
        try:
            if isinstance(role_name, dict) and "name" in role_name:
                _role_name = role_name["name"]
            else:
                _role_name = role_name

            role, created = get_or_create_normalized(Roles, _role_name)
            roles_to_set.append(role)
        except (Roles.MultipleObjectsReturned, ValueError):
            return Response(
                {"detail": f"Invalid role: {_role_name}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    talent_profile.role.set(roles_to_set)
    talent_profile.save()

    return Response({"status": True, "detail": "Account Details Updated."}, status=status.HTTP_200_OK)



@api_view(["POST"])
def update_profile_skills_roles(request):
    userprofile = request.user
    roles = request.data.get("department")
    skills = request.data.get("skills")

    roles_to_set = (
        []
    )  # This list will hold the role objects to be set to the MemberProfile
    for role_name in roles:
        try:
            # Try to get the role by name, and if it doesn't exist, create it.

            # Get the name of the role based on the different datatypes
            # we can get in the codebase
            if "name" in role_name and role_name["name"]:
                dep_name = role_name["name"]
            else:
                dep_name = role_name

            # role = Department.objects.get_or_create(name=dep_name)
            role, create = get_or_create_normalized(Department, dep_name)
            roles_to_set.append(role)
        except (Department.MultipleObjectsReturned, ValueError) as e:
            print(e)
            # Handle the case where multiple roles are found with the same name or
            # where the name is invalid (for instance, if name is a required field
            # and it's None or an empty string).
            return Response(
                {"detail": f"Invalid department: {role_name}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    skills_to_set = (
        []
    )  # This list will hold the role objects to be set to the MemberProfile
    for skill in skills:
        try:
            # Try to get the role by name, and if it doesn't exist, create it.
            if isinstance(skill, str):
                name = skill
            else:
                name = skill["name"]

            skill, create = get_or_create_normalized(Skill, name)
            skills_to_set.append(skill.id)
        except (Skill.MultipleObjectsReturned, ValueError):
            # Handle the case where multiple roles are found with the same name or
            # where the name is invalid (for instance, if name is a required field
            # and it's None or an empty string).
            return Response(
                {"detail": f"Invalid skills: {skill}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    if roles_to_set:
        userprofile.user.department.set(roles_to_set)
    if skills_to_set:
        userprofile.user.skills.set(skills_to_set)
    userprofile.save()

    return Response(
        {"status": True, "detail": "Account Details Updated."},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def update_profile_social_accounts(request):
    userprofile = request.user.userprofile
    userprofile.linkedin = prepend_https_if_not_empty(request.data.get("linkedin"))
    userprofile.instagram = request.data.get("instagram", None)
    userprofile.github = prepend_https_if_not_empty(request.data.get("github"))
    userprofile.twitter = request.data.get("twitter", None)
    userprofile.youtube = prepend_https_if_not_empty(request.data.get("youtube"))
    userprofile.personal = prepend_https_if_not_empty(request.data.get("personal"))
    userprofile.save()

    return Response(
        {"status": True, "detail": "Account Details Updated."},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def update_profile_identity(request):
    # TODO | [CODE CLEAN UP] MOVE TO SERIALIZER
    userprofile = request.user

    identity_sexuality = request.data.get("identity_sexuality")
    gender_identities = request.data.get("gender_identities")
    ethic_identities = request.data.get("ethic_identities")
    disability = request.data.get("disability")
    care_giver = request.data.get("care_giver")
    veteran_status_str = request.data.get("veteran_status")

    sexuality_to_set = (
        []
    )  # This list will hold the role objects to be set to the MemberProfile
    for role_name in identity_sexuality:
        try:
            # Try to get the role by name, and if it doesn't exist, create it.
            if "name" in role_name and role_name["name"]:
                id_name = role_name["name"]
            else:
                id_name = role_name
            name, create = get_or_create_normalized(SexualIdentities, id_name)
            sexuality_to_set.append(name)
        except (SexualIdentities.MultipleObjectsReturned, ValueError):
            # Handle the case where multiple roles are found with the same name or
            # where the name is invalid (for instance, if name is a required field
            # and it's None or an empty string).
            return Response(
                {"detail": f"Invalid sexuality: {role_name}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    gender_to_set = (
        []
    )  # This list will hold the role objects to be set to the MemberProfile
    for role_name in gender_identities:
        try:
            # Try to get the role by name, and if it doesn't exist, create it.
            if "name" in role_name and role_name["name"]:
                id_name = role_name["name"]
            else:
                id_name = role_name
            name, created = get_or_create_normalized(GenderIdentities, id_name)
            # name, created = GenderIdentities.objects.get(name=id_name)
            gender_to_set.append(name)
        except (Roles.MultipleObjectsReturned, ValueError):
            logger.error(ValueError)
            # Handle the case where multiple roles are found with the same name or
            # where the name is invalid (for instance, if name is a required field
            # and it's None or an empty string).
            return Response(
                {"detail": f"Invalid name: {role_name}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    ethic_to_set = (
        []
    )  # This list will hold the role objects to be set to the MemberProfile
    for role_name in ethic_identities:
        try:
            # Try to get the role by name, and if it doesn't exist, create it.
            if "name" in role_name and role_name["name"]:
                id_name = role_name["name"]
            else:
                id_name = role_name
            role, create = get_or_create_normalized(EthicIdentities, id_name)
            ethic_to_set.append(role)
        except (Roles.MultipleObjectsReturned, ValueError):
            # Handle the case where multiple roles are found with the same name or
            # where the name is invalid (for instance, if name is a required field
            # and it's None or an empty string).
            return Response(
                {"detail": f"Invalid name: {role_name}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    if sexuality_to_set:
        userprofile.userprofile.identity_sexuality.set(sexuality_to_set)
    if gender_to_set:
        userprofile.userprofile.identity_gender.set(gender_to_set)
    if ethic_to_set:
        userprofile.userprofile.identity_ethic.set(ethic_to_set)
    if disability:
        userprofile.userprofile.disability = bool(disability)
    if care_giver:
        userprofile.userprofile.care_giver = bool(care_giver)
    if veteran_status_str:
        userprofile.userprofile.veteran_status = veteran_status_str

    userprofile.userprofile.is_identity_sexuality_displayed = request.data.get(
        "is_identity_sexuality_displayed"
    )
    userprofile.userprofile.is_identity_gender_displayed = request.data.get(
        "is_identity_gender_displayed"
    )
    userprofile.userprofile.is_identity_ethic_displayed = request.data.get(
        "is_identity_ethic_displayed"
    )
    userprofile.userprofile.is_disability_displayed = request.data.get(
        "is_disability_displayed"
    )
    userprofile.userprofile.is_care_giver_displayed = request.data.get(
        "is_care_giver_displayed"
    )
    userprofile.userprofile.is_veteran_status_displayed = request.data.get(
        "is_veteran_status_displayed"
    )

    userprofile.save()
    userprofile.userprofile.save()

    return Response(
        {"status": True, "detail": "Account Details Updated."},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def update_profile_notifications(request):
    userprofile = request.user.userprofile

    marketing_jobs = request.data.get("marketing_jobs")
    marketing_events = request.data.get("marketing_events")
    marketing_org_updates = request.data.get("marketing_org_updates")
    marketing_identity_based_programing = request.data.get(
        "marketing_identity_based_programing"
    )
    marketing_monthly_newsletter = request.data.get("marketing_monthly_newsletter")

    userprofile.marketing_jobs = bool(marketing_jobs)
    userprofile.marketing_events = bool(marketing_events)
    userprofile.marketing_org_updates = bool(marketing_org_updates)
    userprofile.marketing_identity_based_programing = bool(
        marketing_identity_based_programing
    )
    userprofile.marketing_monthly_newsletter = bool(marketing_monthly_newsletter)

    userprofile.save()

    return Response(
        {"status": True, "detail": "Account Details Updated."},
        status=status.HTTP_200_OK,
    )


@csrf_exempt
@require_http_methods(["POST"])
def create_new_user(request):
    """
    Create a new user. This view handles the POST request to register a new user.
    It performs input validation, user creation, and sending a welcome email.
    """
    try:
        data = json.loads(request.body)
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email", "").lower()
        password = data.get("password")

        if not all([first_name, last_name, email, password]):
            return JsonResponse(
                {"status": False, "error": "Missing required parameters"}, status=400
            )

        if CustomUser.objects.filter(email=email).exists():
            return JsonResponse(
                {"status": False, "message": "Email already in use"}, status=400
            )

        with transaction.atomic():
            user, token = create_user_account(first_name, last_name, email, password)

            try:
                send_welcome_email(user.email, user.first_name)
                user.is_email_confirmation_sent = True
            except Exception as e:
                logger.warning(f"Failed to send welcome email to {email}: {str(e)}")
                # We're not raising an exception here, allowing the user creation to proceed

            user.save()

            try:
                msg = f":new: *New Member Signup* :new:\n\n*Name* {first_name}\n\n"
                post_message("GL4BCC2HK", msg)
            except Exception as e:
                logger.warning(f"Failed to post Slack message: {str(e)}")
                # We're not raising an exception here, as it's not critical for user creation

        return JsonResponse({"status": True, "message": "User created successfully", "token": token}, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"status": False, "error": "Invalid JSON in request body"}, status=400)
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}", exc_info=True)
        return JsonResponse({"status": False, "message": "Unable to create user"}, status=500)


@csrf_exempt
def create_new_company(request):
    """
    Create a new company user. This view handles the POST request to register a new user.
    It performs input validation, user creation, and sending a welcome email.
    """
    if request.method != "POST":
        return JsonResponse(
            {"status": False, "error": "Invalid request method"}, status=405
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError as e:
        logger.error("Error decoding JSON data: %s", str(e))
        return JsonResponse({"status": False, "error": "Invalid JSON data"}, status=400)

    first_name, last_name, email, password, company_name = (
        data.get("first_name"),
        data.get("last_name"),
        data.get("email", "").lower(),
        data.get("password"),
        data.get("company_name"),
    )

    if not all([first_name, last_name, email, password, company_name]):
        return JsonResponse(
            {"status": False, "error": "Missing required parameters"}, status=400
        )

    if CustomUser.objects.filter(email=email).exists():
        return JsonResponse(
            {"status": False, "message": "Email already in use"}, status=400
        )

    try:
        with transaction.atomic():
            user, token = create_user_account(first_name, last_name, email, password, is_company=True)
            company_profile = CompanyProfile(
                account_creator=user,
                company_name=company_name
            )
            company_profile.save()
            company_profile.account_owner.add(user)
            company_profile.hiring_team.add(user)
            header_token = request.headers.get("Authorization", None)

            try:
                response = requests.post(
                    f'{os.environ["TC_API_URL"]}company/new/onboarding/create-accounts/',
                    data=json.dumps({"companyId": company_profile.id}),
                    headers={'Content-Type': 'application/json'}, verify=True)
                response.raise_for_status()
            except requests.RequestException as e:
                logger.error("Failed to create external accounts: %s", str(e))
                transaction.set_rollback(True)
                return JsonResponse(
                    {"status": False, "error": "Failed to communicate with external service"},
                    status=502  # Bad Gateway indicates issues with external service
                )

            try:
                send_welcome_email(user.email, user.first_name, company_name, user, get_current_site(request), request)
            except Exception as e:
                logger.error("Failed to send welcome email: %s", str(e))
                transaction.set_rollback(True)
                return JsonResponse(
                    {"status": False, "error": "Failed to send welcome email"},
                    status=500
                )

            return JsonResponse({"status": True, "message": "User created successfully", "token": token}, status=201)

    except Exception as e:
        logger.error("Error while creating user: %s", str(e))
        return JsonResponse({"status": False, "message": "Unable to create user"}, status=500)


class LogoutView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        request._auth.delete()
        user_logged_out.send(
            sender=request.user.__class__, request=request, user=request.user
        )
        return Response(None, status=status.HTTP_204_NO_CONTENT)


def create_user_account(first_name, last_name, email, password, is_company=False, request=None):
    """
    Create a new CustomUser account.
    """
    user = CustomUser(
        first_name=first_name,
        last_name=last_name,
        email=email,
        is_slack_active=False,
        password=make_password(password),
        is_company_account=is_company
    )
    user.save()
    _, token = AuthToken.objects.create(user)
    if not is_company:
        user.is_member = True

    user.save()
    return user, token


def send_welcome_email(email, first_name, company_name=None, user=None, current_site=None, request=None):
    """
    Send a welcome email to the new user.
    """
    if company_name:
        token = default_token_generator.make_token(user)

        # Create the email
        mail_subject = 'Activate your account.'
        activation_link = f'{os.environ["FRONTEND_URL"]}new/confirm-account/{urlsafe_base64_encode(force_bytes(user.pk))}/{token}/'

        context = {
            'username': first_name,
            'activation_link': activation_link,
        }

        message = render_to_string('emails/acc_active_email.txt', context=context)
        email_msg = EmailMessage(mail_subject, message, 'notifications@app.techbychocie.org', [user.email])
        email_msg.extra_headers = {
            'email_template': 'emails/acc_active_email.html',
            'token': token,
            'username': first_name,
            'activation_link': activation_link,
        }
        try:
            email_msg.send()
        except Exception as e:
            print("Error while sending emails: ", str(e))
    else:
        template_id = "d-342822c240ed43778ba9e94a04fb10cf"
        dynamic_template_data = {"first_name": first_name}

        email_data = {
            "subject": "Welcome to Our Platform",
            "recipient_emails": [email],
            "template_id": template_id,
            "dynamic_template_data": dynamic_template_data,
        }

        send_dynamic_email(email_data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def soft_delete_user(request, user_id):
    """
    Soft delete a user account by setting is_active to False.

    This view is only accessible by admin users. It deactivates a user account,
    logs the action, and removes the user from external services like Slack and ConvertKit.

    Args:
        request (HttpRequest): The HTTP request object.
        user_id (int): The ID of the user to be soft-deleted.

    Returns:
        Response: A DRF Response object with the result of the operation.

    Raises:
        CustomUser.DoesNotExist: If no user is found with the given ID.
        ValidationError: If an invalid deletion reason is provided.
    """
    reason = request.data.get('reason')

    try:
        with transaction.atomic():
            user = CustomUser.objects.get(id=user_id)

            if not user.is_active:
                logger.warning(f"Attempted to delete already soft-deleted user: {user.email}")
                return Response({"status": False, "message": "User is already deleted"},
                                status=status.HTTP_400_BAD_REQUEST)
            try:
                user.soft_delete(reason)
                return Response({"status": True, "message": "User soft-deleted successfully"},)
            except Exception as e:
                logger.error("Error while soft-deleting user: %s", str(e))
                return Response({"status": False, "message": str(e)},)

        logger.info(f"User {user.email} soft deleted successfully. Reason: {reason}")
        return Response({"status": True, "message": f"User soft deleted successfully. Reason: {reason}"},
                        status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        logger.error(f"Attempted to delete non-existent user with ID: {user_id}")
        return Response({"status": False, "error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        logger.error(f"Invalid deletion reason for user {user_id}: {str(e)}")
        return Response({"status": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception(f"Unexpected error when soft-deleting user {user_id}: {str(e)}")
        return Response({"status": False, "error": "An unexpected error occurred"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def restore_user(request, user_id):
    """
    Restore a soft-deleted user account by setting is_active to True.

    This view is only accessible by admin users. It reactivates a previously soft-deleted user account.

    Args:
        request (HttpRequest): The HTTP request object.
        user_id (int): The ID of the user to be restored.

    Returns:
        Response: A DRF Response object with the result of the operation.

    Raises:
        CustomUser.DoesNotExist: If no user is found with the given ID.
    """
    try:
        with transaction.atomic():
            user = CustomUser.objects.get(id=user_id)

            if user.is_active:
                logger.warning(f"Attempted to restore non-deleted user: {user.email}")
                return Response({"status": False, "message": "User is not deleted"}, status=status.HTTP_400_BAD_REQUEST)

            user.restore()

        logger.info(f"User {user.email} restored successfully")
        return Response({"status": True, "message": "User restored successfully"}, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        logger.error(f"Attempted to restore non-existent user with ID: {user_id}")
        return Response({"status": False, "error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception(f"Unexpected error when restoring user {user_id}: {str(e)}")
        return Response({"status": False, "error": "An unexpected error occurred"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
