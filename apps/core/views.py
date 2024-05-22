import json
import logging
import os

import requests
from django.contrib.auth import user_logged_out
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db import transaction
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from knox.auth import AuthToken, TokenAuthentication
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    throttle_classes,
    parser_classes,
    permission_classes,
)
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

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
from apps.mentorship.models import MentorshipProgramProfile, MentorRoster, MenteeProfile
from apps.mentorship.serializer import (
    MentorRosterSerializer,
    MentorshipProgramProfileSerializer,
)
from apps.member.models import MemberProfile
from utils.emails import send_dynamic_email
from utils.slack import fetch_new_posts, send_invite

logger = logging.getLogger(__name__)


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


@api_view(["GET"])
def get_user_data(request):
    user = request.user
    userprofile = get_object_or_404(UserProfile, user=user)
    userprofile_json_data = UserProfileSerializer(userprofile).data

    # Initialize empty data structures for optional response data
    mentor_data, mentee_data, mentor_roster_data = {}, {}, {}
    talentprofile_json_data = None

    response_data = {
        "status": True,
        "user_info": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "userprofile": userprofile_json_data,
            # "talentprofile" and "current_company" will be conditionally added
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
        "mentor_details": mentor_data,
        "mentee_details": mentee_data,
        "mentor_roster_data": mentor_roster_data,
    }

    # Conditional data based on user's roles
    if user.is_mentor_application_submitted:
        mentor_application = get_object_or_404(MentorshipProgramProfile, user=user)
        mentor_data = MentorshipProgramProfileSerializer(mentor_application).data

    if user.is_mentee:
        mentee_profile = get_object_or_404(MenteeProfile, user=user)
        mentee_data = {"id": mentee_profile.id}
        mentorship_roster = MentorRoster.objects.filter(mentee=mentee_profile)
        if mentorship_roster.exists():
            mentor_roster_data = MentorRosterSerializer(mentorship_roster, many=True).data

    talent_profile = MemberProfile.objects.filter(user=user).first()
    if talent_profile:
        talentprofile_json_data = TalentProfileSerializer(talent_profile).data
        response_data["user_info"]["talentprofile"] = talentprofile_json_data

    # Handle company account logic
    if user.is_company_account:
        company_account_details = get_object_or_404(CompanyProfile, account_owner=user)
        local_company_data = CompanyProfileSerializer(company_account_details).data

        # Make an external request for additional company details
        company_id = company_account_details.id
        full_company_details_url = f'{os.environ["TC_API_URL"]}core/api/company/details/?company_id={company_id}'
        response = requests.get(full_company_details_url)
        if response.status_code == 200:
            company_account_data = response.json()
            # Append local company data to the fetched company data
            company_account_data["company_profile"] = local_company_data
        else:
            company_account_data = {"error": "Could not fetch company details"}

        response_data["company_account_data"] = company_account_data

    return Response(response_data)


def get_company_data(user_details):
    company = get_object_or_404(CompanyProfile, account_owner=user_details)
    return CompanyProfileSerializer(company).data


@api_view(["GET"])
def get_announcement(request):
    try:
        slack_msg = fetch_new_posts("CELK4L5FW", 1)
        if slack_msg:
            return Response({"announcement": slack_msg}, status=status.HTTP_200_OK)
        else:
            print(f"Did not get a new slack message")
            return Response(
                {"message": "No new messages."}, status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        print(f"Error pulling slack message: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
                MentorshipProgramProfile.objects.create(user=user)
                request.user.is_mentee = user_data["is_mentee"]
                request.user.is_mentor = user_data["is_mentor"]
            request.user.is_member_onboarding_complete = True
            request.user.is_company_review_access_active = True
            request.user.save()
            # send slack invite
            try:
                send_invite(user.email)
                request.user.is_slack_invite_sent = True
                request.user.save()
            except Exception as e:
                request.user.is_slack_invite_sent = False
                print(e)

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
    # Handling existing company.
    company_details = request.data.get("select_company", None)

    if company_details:
        try:
            company = CompanyProfile.objects.get(id=company_details["id"])
        except CompanyProfile.DoesNotExist:
            return Response(
                {"status": False, "detail": "Company does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:  # Handling new company.
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

    # Updating the current employee for the company.
    user = request.user
    company.current_employees.add(user)
    company.save()

    # Updating talent profile.
    talent_profile = get_object_or_404(MemberProfile, user=request.user)
    role_names = request.data.get("job_roles")

    roles_to_set = (
        []
    )  # This list will hold the role objects to be set to the MemberProfile
    for role_name in role_names:
        try:
            # Try to get the role by name, and if it doesn't exist, create it.
            role, created = Roles.objects.get_or_create(name=role_name["name"])
            roles_to_set.append(role)
        except (Roles.MultipleObjectsReturned, ValueError):
            # Handle the case where multiple roles are found with the same name or
            # where the name is invalid (for instance, if name is a required field
            # and it's None or an empty string).
            return Response(
                {"detail": f"Invalid role: {role_name}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    talent_profile.role.set(roles_to_set)
    talent_profile.save()

    return Response({"detail": "Account Details Updated."}, status=status.HTTP_200_OK)


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
            role = Department.objects.get(name=role_name["name"])
            roles_to_set.append(role)
        except (Department.MultipleObjectsReturned, ValueError):
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
            name = Skill.objects.get(name=skill["name"])
            skills_to_set.append(name.pk)
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
    userprofile.linkedin = "https://" + request.data.get("linkedin")
    userprofile.instagram = request.data.get("instagram")
    userprofile.github = "https://" + request.data.get("github")
    userprofile.twitter = request.data.get("twitter")
    userprofile.youtube = "https://" + request.data.get("youtube")
    userprofile.personal = "https://" + request.data.get("personal")
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
            role = SexualIdentities.objects.get(name=role_name)
            sexuality_to_set.append(role)
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
            role = GenderIdentities.objects.get(name=role_name)
            gender_to_set.append(role)
        except (Roles.MultipleObjectsReturned, ValueError):
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
            role = EthicIdentities.objects.get(name=role_name)
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
def create_new_user(request):
    """
    Create a new user. This view handles the POST request to register a new user.
    It performs input validation, user creation, and sending a welcome email.
    """
    if request.method != "POST":
        return JsonResponse(
            {"status": False, "error": "Invalid request method"}, status=405
        )

    data = json.loads(request.body)
    first_name, last_name, email, password = (
        data.get("first_name"),
        data.get("last_name"),
        data.get("email", "").lower(),
        data.get("password"),
    )

    if not all([first_name, last_name, email, password]):
        return JsonResponse(
            {"status": False, "error": "Missing required parameters"}, status=400
        )

    if CustomUser.objects.filter(email=email).exists():
        return JsonResponse(
            {"status": False, "message": "Email already in use"}, status=400
        )
    try:
        user, token = create_user_account(first_name, last_name, email, password)
        try:
            send_welcome_email(user.email, user.first_name)
            user.is_email_confirmation_sent = True
            user.save()
            return JsonResponse({"status": True, "message": "User created successfully", "token": token}, status=201)
        except Exception as e:
            print("Error while saving user: ", str(e))
            return JsonResponse({"status": False, "message": "Unable to create user"}, status=500)
    except Exception as e:
        print("Error while saving user: ", str(e))
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
        print(context)

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
