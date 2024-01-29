import json
import logging

from django.contrib.auth import user_logged_out
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Prefetch
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from knox.auth import AuthToken, TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes, parser_classes
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.company.models import Roles, JobLevel, CompanyProfile, Skill, Department, CompanyTypes, Industries, \
    SalaryRange, COMPANY_SIZE, ON_SITE_REMOTE
from apps.core.models import UserProfile, PronounsIdentities, EthicIdentities, GenderIdentities, SexualIdentities, \
    CommunityNeeds, CustomUser
from apps.core.serializers import UserProfileSerializer, CustomAuthTokenSerializer, \
    UpdateProfileAccountDetailsSerializer, CompanyProfileSerializer, UpdateCustomUserSerializer, \
    TalentProfileRoleSerializer, TalentProfileSerializer
from apps.core.util import extract_user_data, extract_company_data, extract_profile_data, extract_talent_data, \
    create_or_update_user, create_or_update_talent_profile, create_or_update_user_profile, \
    create_or_update_company_connection
from apps.mentorship.models import MentorshipProgramProfile, MentorRoster, MenteeProfile
from apps.mentorship.serializer import MentorRosterSerializer, MentorshipProgramProfileSerializer
from apps.talent.models import TalentProfile
from apps.talent.serializers import UpdateTalentProfileSerializer
from utils.emails import send_dynamic_email
from utils.helper import prepend_https_if_not_empty
from utils.slack import fetch_new_posts, send_invite

logger = logging.getLogger(__name__)


class LoginThrottle(UserRateThrottle):
    rate = '5/min'


@api_view(['POST'])
@throttle_classes([LoginThrottle])
def login_api(request):
    serializer = CustomAuthTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    # userprofile = UserProfile.objects.get(user=user.id)
    # userprofile_serializer = UserProfileSerializer(userprofile)
    # userprofile_json_data = userprofile_serializer.data
    # userprofile.timezone = request.data['timezone']
    # userprofile.save()
    # create a token to track login
    _, token = AuthToken.objects.create(user)

    response = JsonResponse({
        'status': True,
        'user_info': {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'userprofile': [],
            # 'userprofile': userprofile_json_data
        },
        'account_info': {
            'is_staff': user.is_staff,
            'is_recruiter': user.is_recruiter,
            'is_member': user.is_member,
            'is_mentor': user.is_mentor,
            'is_mentee': user.is_mentee,
            'is_speaker': user.is_speaker,
            'is_volunteer': user.is_volunteer,
            'is_mentor_profile_active': user.is_mentor_profile_active,
            'is_mentor_training_complete': user.is_mentor_training_complete,
            'is_mentor_profile_approved': user.is_mentor_profile_approved,
            'is_mentor_application_submitted': user.is_mentor_application_submitted,
            'is_talent_source_beta': user.is_talent_source_beta,
            'is_team': user.is_team,
            'is_community_recruiter': user.is_community_recruiter,
            'is_company_account': user.is_company_account,
            'is_partnership': user.is_partnership,
        },
        'token': token
    })

    # Set secure cookie
    response.set_cookie('auth_token', token, secure=False,
                        httponly=True, domain='localhost')  # httponly=True to prevent access by JavaScript

    return response


@api_view(['GET'])
def get_user_data(request):
    user = request.user
    userprofile = UserProfile.objects.get(user_id=user.id)
    userprofile_serializer = UserProfileSerializer(userprofile)
    userprofile_json_data = userprofile_serializer.data
    mentor_data = {}
    mentee_data = {}
    mentor_roster_data = {}

    # Get mentor data
    # if user.is_mentor and user.is_mentor_application_submitted:
    if user.is_mentor_application_submitted:
        mentor_application = MentorshipProgramProfile.objects.get(user=user)
        mentor_serializer = MentorshipProgramProfileSerializer(mentor_application)
        mentor_data = mentor_serializer.data
    if user.is_mentee:
        mentor_application = MentorshipProgramProfile.objects.get(user=user)
        mentee_profile = MenteeProfile.objects.get(user_id=user.id)
        mentee_data = {
            'id': mentee_profile.id,
            # 'mentee_support_areas': mentor_application.mentee_profile.mentee_support_areas,
        }

        # Check to see if the user is connected with any mentors
        mentee_profiles = MenteeProfile.objects.get(user=request.user)
        mentorship_roster = MentorRoster.objects.filter(mentee=mentee_profiles.id)

        if mentorship_roster:
            serializer = MentorRosterSerializer(mentorship_roster, many=True)
            mentor_roster_data = serializer.data

    # Fetch and Serialize TalentProfile Data
    try:
        talentprofile = TalentProfile.objects.get(user=user.id)  # Fetch TalentProfile related to the user
        talentprofile_serializer = TalentProfileSerializer(talentprofile)  # Serialize TalentProfile data
        talentprofile_json_data = talentprofile_serializer.data  # Convert serialized data to JSON
    except TalentProfile.DoesNotExist:  # Handle the case when TalentProfile does not exist for the user
        talentprofile_json_data = None

    try:
        current_company = CompanyProfile.objects.get(current_employees=request.user)
    except CompanyProfile.DoesNotExist:
        current_company = None

    return Response({
        'status': True,
        'user_info': {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'userprofile': userprofile_json_data,
            'talentprofile': talentprofile_json_data,
            "current_company": {
                "id": current_company.id if current_company else None,
                "company_name": current_company.company_name if current_company else None
            }
        },
        'account_info': {
            'is_staff': user.is_staff,
            'is_recruiter': user.is_recruiter,
            'is_member': user.is_member,
            'is_mentor': user.is_mentor,
            'is_mentee': user.is_mentee,
            'is_mentor_profile_active': user.is_mentor_profile_active,
            'is_mentor_profile_removed': user.is_mentor_profile_removed,
            'is_mentor_training_complete': user.is_mentor_training_complete,
            'is_mentor_interviewing': user.is_mentor_interviewing,
            'is_mentor_profile_paused': user.is_mentor_profile_paused,
            'is_mentor_profile_approved': user.is_mentor_profile_approved,
            'is_mentor_application_submitted': user.is_mentor_application_submitted,
            'is_speaker': user.is_speaker,
            'is_volunteer': user.is_volunteer,
            'is_team': user.is_team,
            'is_community_recruiter': user.is_community_recruiter,
            'is_company_account': user.is_company_account,
            'is_partnership': user.is_partnership,
        },
        'mentor_details': mentor_data,
        'mentee_details': mentee_data,
        'mentor_roster_data': mentor_roster_data
    })


@api_view(['GET'])
def get_announcement(request):
    try:
        slack_msg = fetch_new_posts('CELK4L5FW', 1)
        if slack_msg:
            return Response({'announcement': slack_msg}, status=status.HTTP_200_OK)
        else:
            print(f'Did not get a new slack message')
            return Response({"message": "No new messages."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f'Error pulling slack message: {str(e)}')
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @login_required
@parser_classes([MultiPartParser])
@api_view(['PATCH'])
def create_new_member(request):
    if request.user.is_member_onboarding_complete:
        return Response(
            {'status': False, 'message': 'Member has already been created for this user.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        data = request.data
        user_data = extract_user_data(data)
        company_data = extract_company_data(data)
        profile_data = extract_profile_data(data, request.FILES)
        talent_data = extract_talent_data(data, request.FILES)

        with transaction.atomic():
            user = create_or_update_user(request.user, user_data)
            talent_profile = create_or_update_talent_profile(user, talent_data)
            user_profile = create_or_update_user_profile(user, profile_data)
            user_company_connection = create_or_update_company_connection(user, company_data)

            request.user.is_member_onboarding_complete = True
            request.user.save()

            if user_data['is_mentee'] or user_data['is_mentor']:
                MentorshipProgramProfile.objects.create(user=user)
            # send slack invite
            send_invite(user.email)
            return Response(
                {'status': True, 'message': 'User, TalentProfile, and UserProfile created successfully!'},
                status=status.HTTP_200_OK
            )

    except Exception as e:
        # Handle specific known exceptions
        return Response({'status': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        # Handle unexpected exceptions
        print(e)
        return Response({'status': False, 'error': 'An unexpected error occurred.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_new_company_data(request):
    return Response({
        'status': True,
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
                        "options": None
                    },
                    {
                        "order": 1,
                        "label": "Please details your would like to receive marketing about",
                        "key": None,
                        "helper_text": None,
                        "type": "header",
                        "options": None
                    },
                    {
                        "order": 2,
                        "label": "Our Monthly Newsletter",
                        "key": "marketing_monthly_newsletter",
                        "helper_text": None,
                        "type": "checkbox",
                        "options": None
                    },
                    {
                        "order": 3,
                        "label": "Community Events",
                        "key": "marketing_events",
                        "helper_text": None,
                        "type": "checkbox",
                        "options": None
                    },
                    {
                        "order": 4,
                        "label": "Interest Based Programing",
                        "key": "marketing_identity_based_programing",
                        "helper_text": None,
                        "type": "checkbox",
                        "options": None
                    },
                    {
                        "order": 5,
                        "label": "Open Jobs & Job Hunting Tips",
                        "key": "marketing_jobs",
                        "helper_text": None,
                        "type": "checkbox",
                        "options": None
                    },
                    {
                        "order": 5,
                        "label": "Community Updates",
                        "key": "marketing_org_updates",
                        "helper_text": None,
                        "type": "checkbox",
                        "options": None
                    },
                ]
            },
        ]
    })


@api_view(['POST'])
def update_profile_account_details(request):
    user = request.user
    try:
        profile = user.userprofile
    except TalentProfile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        serializer = UpdateProfileAccountDetailsSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'message': 'Form Saved'}, status=status.HTTP_200_OK)
        return Response({'status': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def update_profile_work_place(request):
    # Handling existing company.
    company_details = request.data.get('select_company', None)

    if company_details:
        try:
            company = CompanyProfile.objects.get(id=company_details['id'])
        except CompanyProfile.DoesNotExist:
            return Response({'status': False, 'detail': 'Company does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
    else:  # Handling new company.
        company_serializer = CompanyProfileSerializer(data=request.data, context={'request': request})
        if company_serializer.is_valid():
            company = company_serializer.save()
        else:
            return Response({'status': False, 'message': company_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # Updating the current employee for the company.
    user = request.user
    company.current_employees.add(user)
    company.save()

    # Updating talent profile.
    talent_profile = get_object_or_404(TalentProfile, user=request.user)
    role_names = request.data.get('job_roles')

    roles_to_set = []  # This list will hold the role objects to be set to the TalentProfile
    for role_name in role_names:
        try:
            # Try to get the role by name, and if it doesn't exist, create it.
            role, created = Roles.objects.get_or_create(name=role_name['name'])
            roles_to_set.append(role)
        except (Roles.MultipleObjectsReturned, ValueError):
            # Handle the case where multiple roles are found with the same name or
            # where the name is invalid (for instance, if name is a required field
            # and it's None or an empty string).
            return Response({'detail': f'Invalid role: {role_name}'}, status=status.HTTP_400_BAD_REQUEST)
    talent_profile.role.set(roles_to_set)
    talent_profile.save()

    return Response({'detail': 'Account Details Updated.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def update_profile_skills_roles(request):
    userprofile = request.user
    roles = request.data.get('department')
    skills = request.data.get('skills')

    roles_to_set = []  # This list will hold the role objects to be set to the TalentProfile
    for role_name in roles:
        try:
            # Try to get the role by name, and if it doesn't exist, create it.
            role = Department.objects.get(name=role_name['name'])
            roles_to_set.append(role)
        except (Department.MultipleObjectsReturned, ValueError):
            # Handle the case where multiple roles are found with the same name or
            # where the name is invalid (for instance, if name is a required field
            # and it's None or an empty string).
            return Response({'detail': f'Invalid department: {role_name}'}, status=status.HTTP_400_BAD_REQUEST)

    skills_to_set = []  # This list will hold the role objects to be set to the TalentProfile
    for skill in skills:
        try:
            # Try to get the role by name, and if it doesn't exist, create it.
            name = Skill.objects.get(name=skill['name'])
            skills_to_set.append(name.pk)
        except (Skill.MultipleObjectsReturned, ValueError):
            # Handle the case where multiple roles are found with the same name or
            # where the name is invalid (for instance, if name is a required field
            # and it's None or an empty string).
            return Response({'detail': f'Invalid skills: {skill}'}, status=status.HTTP_400_BAD_REQUEST)

    if roles_to_set:
        userprofile.user.department.set(roles_to_set)
    if skills_to_set:
        userprofile.user.skills.set(skills_to_set)
    userprofile.save()

    return Response({'status': True, 'detail': 'Account Details Updated.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def update_profile_social_accounts(request):
    userprofile = request.user.userprofile
    userprofile.linkedin = 'https://' + request.data.get('linkedin')
    userprofile.instagram = request.data.get('instagram')
    userprofile.github = 'https://' + request.data.get('github')
    userprofile.twitter = request.data.get('twitter')
    userprofile.youtube = 'https://' + request.data.get('youtube')
    userprofile.personal = 'https://' + request.data.get('personal')
    userprofile.save()

    return Response({'status': True, 'detail': 'Account Details Updated.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def update_profile_identity(request):
    # TODO | [CODE CLEAN UP] MOVE TO SERIALIZER
    userprofile = request.user

    identity_sexuality = request.data.get('identity_sexuality')
    gender_identities = request.data.get('gender_identities')
    ethic_identities = request.data.get('ethic_identities')
    disability = request.data.get('disability')
    care_giver = request.data.get('care_giver')
    veteran_status_str = request.data.get('veteran_status')

    sexuality_to_set = []  # This list will hold the role objects to be set to the TalentProfile
    for role_name in identity_sexuality:
        try:
            # Try to get the role by name, and if it doesn't exist, create it.
            role = SexualIdentities.objects.get(identity=role_name['identity'])
            sexuality_to_set.append(role)
        except (SexualIdentities.MultipleObjectsReturned, ValueError):
            # Handle the case where multiple roles are found with the same name or
            # where the name is invalid (for instance, if name is a required field
            # and it's None or an empty string).
            return Response({'detail': f'Invalid sexuality: {role_name}'}, status=status.HTTP_400_BAD_REQUEST)

    gender_to_set = []  # This list will hold the role objects to be set to the TalentProfile
    for role_name in gender_identities:
        try:
            # Try to get the role by name, and if it doesn't exist, create it.
            role = GenderIdentities.objects.get(gender=role_name['gender'])
            gender_to_set.append(role)
        except (Roles.MultipleObjectsReturned, ValueError):
            # Handle the case where multiple roles are found with the same name or
            # where the name is invalid (for instance, if name is a required field
            # and it's None or an empty string).
            return Response({'detail': f'Invalid gender: {role_name}'}, status=status.HTTP_400_BAD_REQUEST)

    ethic_to_set = []  # This list will hold the role objects to be set to the TalentProfile
    for role_name in ethic_identities:
        try:
            # Try to get the role by name, and if it doesn't exist, create it.
            role = EthicIdentities.objects.get(ethnicity=role_name['ethnicity'])
            ethic_to_set.append(role)
        except (Roles.MultipleObjectsReturned, ValueError):
            # Handle the case where multiple roles are found with the same name or
            # where the name is invalid (for instance, if name is a required field
            # and it's None or an empty string).
            return Response({'detail': f'Invalid ethnicity: {role_name}'}, status=status.HTTP_400_BAD_REQUEST)
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

    userprofile.userprofile.is_identity_sexuality_displayed = request.data.get('is_identity_sexuality_displayed')
    userprofile.userprofile.is_identity_gender_displayed = request.data.get('is_identity_gender_displayed')
    userprofile.userprofile.is_identity_ethic_displayed = request.data.get('is_identity_ethic_displayed')
    userprofile.userprofile.is_disability_displayed = request.data.get('is_disability_displayed')
    userprofile.userprofile.is_care_giver_displayed = request.data.get('is_care_giver_displayed')
    userprofile.userprofile.is_veteran_status_displayed = request.data.get('is_veteran_status_displayed')

    userprofile.save()
    userprofile.userprofile.save()

    return Response({'status': True, 'detail': 'Account Details Updated.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def update_profile_notifications(request):
    userprofile = request.user.userprofile

    marketing_jobs = request.data.get('marketing_jobs')
    marketing_events = request.data.get('marketing_events')
    marketing_org_updates = request.data.get('marketing_org_updates')
    marketing_identity_based_programing = request.data.get('marketing_identity_based_programing')
    marketing_monthly_newsletter = request.data.get('marketing_monthly_newsletter')

    userprofile.marketing_jobs = bool(marketing_jobs)
    userprofile.marketing_events = bool(marketing_events)
    userprofile.marketing_org_updates = bool(marketing_org_updates)
    userprofile.marketing_identity_based_programing = bool(marketing_identity_based_programing)
    userprofile.marketing_monthly_newsletter = bool(marketing_monthly_newsletter)

    userprofile.save()

    return Response({'status': True, 'detail': 'Account Details Updated.'}, status=status.HTTP_200_OK)


@csrf_exempt
def create_new_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email').lower()
        password = data.get('password')

        if not all([first_name, last_name, email, password]):
            return JsonResponse({'status': False, 'error': 'Missing required parameters'}, status=400)

        # Check if a user with this email already exists
        if CustomUser.objects.filter(email=email).exists():
            return JsonResponse({'status': False, 'message': 'Email already in use'}, status=400)

        password = make_password(password)
        user = CustomUser(first_name=first_name, last_name=last_name, email=email, password=password)
        try:
            user.save()

            # response = JsonResponse({'status': True, 'message': 'User created successfully'}, status=201)

            # Create a token to track login
            _, token = AuthToken.objects.create(user)

            user.is_member = True
            user.save()

            # Prepare email data
            email_data = {
                'subject': 'Welcome to Our Platform',
                'recipient_emails': [user.email],
                'template_id': 'd-342822c240ed43778ba9e94a04fb10cf',
                'dynamic_template_data': {
                    'first_name': user.first_name,
                }
            }

            send_dynamic_email(email_data)

            response = JsonResponse({'status': True, 'message': 'User created successfully', 'token': token},
                                    status=201)
            return response
        except Exception as e:
            # Log the exception for debugging
            print("Error while saving user: ", str(e))
            return JsonResponse({'status': False, 'error': 'Unable to create user'}, status=500)

    else:
        return JsonResponse({'status': False, 'error': 'Invalid request method'}, status=405)


class LogoutView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        request._auth.delete()
        user_logged_out.send(sender=request.user.__class__,
                             request=request, user=request.user)
        return Response(None, status=status.HTTP_204_NO_CONTENT)
