import json
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Prefetch
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from knox.auth import AuthToken
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes, parser_classes
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from apps.company.models import Roles, JobLevel, CompanyProfile, Skill, Department, CompanyTypes, Industries, \
    SalaryRange, COMPANY_SIZE, ON_SITE_REMOTE
from apps.core.models import UserProfile, PronounsIdentities, EthicIdentities, GenderIdentities, SexualIdentities, \
    CommunityNeeds, CustomUser
from apps.core.serializers import UserProfileSerializer, CustomAuthTokenSerializer, \
    UpdateProfileAccountDetailsSerializer, CompanyProfileSerializer, UpdateCustomUserSerializer, \
    TalentProfileRoleSerializer, TalentProfileSerializer
from apps.mentorship.models import MentorshipProgramProfile
from apps.talent.models import TalentProfile
from apps.talent.serializers import UpdateTalentProfileSerializer
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

    slack_msg = fetch_new_posts('CELK4L5FW', 1)
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
        'announcement': slack_msg,
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
            'is_speaker': user.is_speaker,
            'is_volunteer': user.is_volunteer,
            'is_team': user.is_team,
            'is_community_recruiter': user.is_community_recruiter,
            'is_company_account': user.is_company_account,
            'is_partnership': user.is_partnership,
        },
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


@api_view(['GET'])
def get_new_member_data(request):
    sexual_identities = list(SexualIdentities.objects.values('identity', 'id'))
    gender_identities = list(GenderIdentities.objects.values('gender', 'id'))
    ethic_identities = list(EthicIdentities.objects.values('ethnicity', 'id'))
    pronouns_identities = list(PronounsIdentities.objects.values('pronouns', 'id'))
    job_skills = list(Skill.objects.values('name', 'skill_type', 'id'))
    community_needs = list(CommunityNeeds.objects.values('name', 'id'))
    job_department = list(Department.objects.values('name', 'id'))
    job_roles = Roles.objects.prefetch_related(Prefetch('job_skill_list')).all()
    job_salary_range = list(SalaryRange.objects.values('range'))
    job_site = [{'name': site[0], 'value': site[1]} for site in ON_SITE_REMOTE]
    company_list = list(CompanyProfile.objects.values('company_name', 'id', 'company_url'))
    company_sizes = [{'name': size[0], 'value': size[1]} for size in COMPANY_SIZE]
    company_types = list(CompanyTypes.objects.values('name', 'id'))
    company_industries = list(Industries.objects.values('name', 'id'))
    how_connection_made_list = UserProfile.HOW_CONNECTION_MADE
    # career_journey_choices = TalentProfile.CAREER_JOURNEY
    career_journey_choices = TalentProfile.CAREER_JOURNEY
    connection_options = []
    career_journey_steps = []
    roles_data = []
    for id, name in career_journey_choices:
        career_journey_steps.append({
            'name': name,
            'id': id
        })

    for connection_type in how_connection_made_list:
        connection_options.append({
            'name': connection_type[1]
        })

    # Iterate over roles and get their skill names.
    for role in job_roles:
        skill_names = [skill.name for skill in role.job_skill_list.all()[:3]]
        roles_data.append({
            'id': role.id,
            'name': role.name,
            'job_skill_list': skill_names
        })

    return Response({
        'status': True,
        "total_companies": len(company_list),
        "sexual_identities": sexual_identities,
        "gender_identities": gender_identities,
        "ethic_identities": ethic_identities,
        "pronouns_identities": pronouns_identities,
        "job_skills": job_skills,
        "community_needs": community_needs,
        "job_department": job_department,
        "job_roles": roles_data,
        "job_salary_range": job_salary_range,
        "job_site": job_site,
        "company_list": company_list,
        "company_sizes": company_sizes,
        "company_types": company_types,
        "company_industries": company_industries,
        "career_journey_choices": career_journey_steps,
        "connection_options": connection_options,
    })


# @login_required
@parser_classes([MultiPartParser])
@api_view(['PATCH'])
def create_new_member(request):
    data = request.data
    user_data = {
        'is_mentee': True if data.get('is_mentee', '') else False,
        'is_mentor': True if data.get('is_mentor', '') else False,
    }

    company_data = {
        'company_name': data.get('company_name', ''),
        'company_url': data.get('company_url', ''),
    }

    profile_data = {
        'linkedin': "https://" + data.get('linkedin', ''),
        'instagram': data.get('instagram', ''),
        'github': "https://" + data.get('github', ''),
        'twitter': data.get('twitter', ''),
        'youtube': "https://" + data.get('youtube', ''),
        'personal': "https://" + data.get('personal', ''),
        'identity_sexuality': data.get('identity_sexuality', '').split(','),
        'identity_gender': data.get('gender_identities', '').split(','),
        'identity_ethic': data.get('identity_ethic', '').split(','),
        'identity_pronouns': data.get('pronouns_identities', '').split(','),
        'disability': True if data.get('disability', '') else False,
        'care_giver': True if data.get('care_giver', '') else False,
        'veteran_status': data.get('veteran_status', ''),
        'how_connection_made': data.get('how_connection_made', '').lower(),
        'is_pronouns_displayed': True if data.get('is_pronouns_displayed', '') else False,
        'marketing_monthly_newsletter': True if data.get('marketing_monthly_newsletter', '') else False,
        'marketing_events': True if data.get('marketing_events', '') else False,
        'marketing_identity_based_programing': True if data.get('marketing_identity_based_programing', '') else False,
        'marketing_jobs': True if data.get('marketing_jobs', '') else False,
        'marketing_org_updates': True if data.get('marketing_org_updates', '') else False,
        'postal_code': data.get('postal_code', ''),
        'tbc_program_interest': data.get('tbc_program_interest', ''),
        'photo': request.FILES['photo'] if 'photo' in request.FILES else None,
    }

    talent_data = {
        'tech_journey': data.get('tech_journey', []),
        'talent_status': data.get('talent_status', False),
        'company_types': data.get('company_types', []).split(',') if data.get('company_types') else '',
        'department': data.get('job_department', []).split(','),
        'role': data.get('job_roles', []).split(','),
        'skills': data.get('job_skills', []).split(','),
        'max_compensation': data.get('max_compensation', []),
        'min_compensation': data.get('min_compensation', []),
        'resume': request.FILES['resume'] if 'resume' in request.FILES else None
    }

    try:
        with transaction.atomic():
            # Create CustomUser object

            user_serializer = UpdateCustomUserSerializer(instance=request.user, data=user_data, partial=True)
            user_serializer.is_valid(raise_exception=True)
            user = user_serializer.save()
            # user = request.user.id
            # user_details = CustomUser.objects.get(id=request.user.id)

            # Handle TalentProfile related fields and create object
            roles_to_set = []  # This list will hold the role objects to be set to the TalentProfile
            for role_name in talent_data['role']:
                try:
                    # Try to get the role by name, and if it doesn't exist, create it.
                    role, created = Roles.objects.get_or_create(name=role_name)
                    roles_to_set.append(role.pk)
                except (Roles.MultipleObjectsReturned, ValueError):
                    # Handle the case where multiple roles are found with the same name or
                    # where the name is invalid (for instance, if name is a required field
                    # and it's None or an empty string).
                    return Response({'detail': f'Invalid role: {role_name}'}, status=status.HTTP_400_BAD_REQUEST)

            company_types_to_set = []  # This list will hold the role objects to be set to the TalentProfile
            if isinstance(talent_data['company_types'], list) and talent_data['company_types']:
                for company_type in talent_data['company_types']:
                    if company_type:  # Check if company_type is not an empty string
                        try:
                            name, created = CompanyTypes.objects.get_or_create(name=company_type)
                            company_types_to_set.append(name.pk)
                        except (CompanyTypes.MultipleObjectsReturned, ValueError):
                            return Response({'detail': f'Invalid company type: {company_type}'},
                                            status=status.HTTP_400_BAD_REQUEST)

            department_to_set = []  # This list will hold the role objects to be set to the TalentProfile
            for department in talent_data['department']:
                try:
                    # Try to get the role by name, and if it doesn't exist, create it.
                    name, created = Department.objects.get_or_create(name=department)
                    department_to_set.append(name.pk)
                except (Department.MultipleObjectsReturned, ValueError):
                    # Handle the case where multiple roles are found with the same name or
                    # where the name is invalid (for instance, if name is a required field
                    # and it's None or an empty string).
                    return Response({'detail': f'Invalid department: {department}'}, status=status.HTTP_400_BAD_REQUEST)

            skills_to_set = []  # This list will hold the role objects to be set to the TalentProfile
            for skill in talent_data['skills']:
                try:
                    # Try to get the role by name, and if it doesn't exist, create it.
                    name, created = Skill.objects.get_or_create(name=skill)
                    skills_to_set.append(name.pk)
                except (Skill.MultipleObjectsReturned, ValueError):
                    # Handle the case where multiple roles are found with the same name or
                    # where the name is invalid (for instance, if name is a required field
                    # and it's None or an empty string).
                    return Response({'detail': f'Invalid role: {skill}'}, status=status.HTTP_400_BAD_REQUEST)

            min_compensation_to_set = []  # This list will hold the role objects to be set to the TalentProfile
            # Check if 'min_compensation' is a list, not empty, and its first element isn't an empty string
            if (isinstance(talent_data['min_compensation'], list) and
                    len(talent_data['min_compensation']) > 0 and
                    talent_data['min_compensation'][0] != ''):

                for comp in talent_data['min_compensation']:
                    try:
                        # Try to get the role by name, and if it doesn't exist, create it.
                        name, created = SalaryRange.objects.get_or_create(id=comp)
                        min_compensation_to_set.append(name.pk)
                    except (SalaryRange.MultipleObjectsReturned, ValueError):
                        # Handle the case where multiple roles are found with the same name or
                        # where the name is invalid (for instance, if name is a required field
                        # and it's None or an empty string).
                        return Response({'detail': f'Invalid salary range: {comp}'}, status=status.HTTP_400_BAD_REQUEST)

            max_compensation_to_set = []  # This list will hold the role objects to be set to the TalentProfile
            # Check if 'min_compensation' is a list, not empty, and its first element isn't an empty string
            if (isinstance(talent_data['max_compensation'], list) and
                    len(talent_data['max_compensation']) > 0 and
                    talent_data['max_compensation'][0] != ''):

                for comp in talent_data['max_compensation']:
                    try:
                        # Try to get the role by name, and if it doesn't exist, create it.
                        name, created = SalaryRange.objects.get_or_create(id=comp)
                        max_compensation_to_set.append(name.pk)
                    except (SalaryRange.MultipleObjectsReturned, ValueError):
                        # Handle the case where multiple roles are found with the same name or
                        # where the name is invalid (for instance, if name is a required field
                        # and it's None or an empty string).
                        return Response({'detail': f'Invalid salary range: {comp}'}, status=status.HTTP_400_BAD_REQUEST)

            talent_data['user'] = user.id  # set the user field in TalentProfile
            talent_data['min_compensation'] = min_compensation_to_set[0] if min_compensation_to_set else 1
            talent_data['max_compensation'] = max_compensation_to_set[0] if max_compensation_to_set else 1
            talent_data['skills'] = skills_to_set
            talent_data['department'] = department_to_set
            talent_data['company_types'] = company_types_to_set
            talent_data['role'] = roles_to_set
            talent_serializer = UpdateTalentProfileSerializer(data=talent_data)
            talent_serializer.is_valid(raise_exception=True)
            talent = talent_serializer.save()

            # Handle UserProfile related fields and create object
            identity_sexuality_to_set = []  # This list will hold the role objects to be set to the TalentProfile
            if profile_data['identity_sexuality'] and not (isinstance(profile_data['identity_sexuality'], list) and len(
                    profile_data['identity_sexuality']) == 1 and profile_data['identity_sexuality'][0] == ''):
                for comp in profile_data['identity_sexuality']:
                    try:
                        # Try to get the role by name, and if it doesn't exist, create it.
                        identity = SexualIdentities.objects.get(identity=comp)
                        identity_sexuality_to_set.append(identity.pk)
                    except (SexualIdentities.MultipleObjectsReturned, ValueError):
                        # Handle the case where multiple roles are found with the same name or
                        # where the name is invalid (for instance, if name is a required field
                        # and it's None or an empty string).
                        return Response({'detail': f'Invalid sexuality: {comp}'}, status=status.HTTP_400_BAD_REQUEST)

            identity_gender_to_set = []  # This list will hold the role objects to be set to the TalentProfile
            if profile_data['identity_gender'] and not (
                    isinstance(profile_data['identity_gender'], list) and len(profile_data['identity_gender']) == 1 and
                    profile_data['identity_gender'][0] == ''):
                for comp in profile_data['identity_gender']:
                    try:
                        # Try to get the role by name, and if it doesn't exist, create it.
                        gender = GenderIdentities.objects.get(gender=comp)
                        identity_gender_to_set.append(gender.pk)
                    except (GenderIdentities.MultipleObjectsReturned, ValueError):
                        # Handle the case where multiple roles are found with the same name or
                        # where the name is invalid (for instance, if name is a required field
                        # and it's None or an empty string).
                        return Response({'detail': f'Invalid gender: {comp}'}, status=status.HTTP_400_BAD_REQUEST)

            identity_ethic_to_set = []  # This list will hold the role objects to be set to the TalentProfile
            if profile_data['identity_ethic'] and not (
                    isinstance(profile_data['identity_ethic'], list) and len(profile_data['identity_ethic']) == 1 and
                    profile_data['identity_ethic'][0] == ''):
                for item in profile_data['identity_ethic']:
                    try:
                        # Try to get the role by name, and if it doesn't exist, create it.
                        ethnicity = EthicIdentities.objects.get(ethnicity=item)
                        identity_ethic_to_set.append(ethnicity.pk)
                    except (EthicIdentities.MultipleObjectsReturned, ValueError):
                        # Handle the case where multiple roles are found with the same name or
                        # where the name is invalid (for instance, if name is a required field
                        # and it's None or an empty string).
                        return Response({'detail': f'Invalid ethnicity: {comp}'}, status=status.HTTP_400_BAD_REQUEST)

            identity_pronouns_to_set = []  # This list will hold the role objects to be set to the TalentProfile
            if profile_data['identity_pronouns'] and not (isinstance(profile_data['identity_pronouns'], list) and len(
                    profile_data['identity_pronouns']) == 1 and profile_data['identity_pronouns'][0] == ''):
                for item in profile_data['identity_pronouns']:
                    try:
                        # Try to get the role by name, and if it doesn't exist, create it.
                        pronouns = PronounsIdentities.objects.get(pronouns=item)
                        identity_pronouns_to_set.append(pronouns.pk)
                    except (PronounsIdentities.MultipleObjectsReturned, ValueError):
                        # Handle the case where multiple roles are found with the same name or
                        # where the name is invalid (for instance, if name is a required field
                        # and it's None or an empty string).
                        return Response({'detail': f'Invalid pronouns: {comp}'}, status=status.HTTP_400_BAD_REQUEST)

            profile_data['user'] = user.id  # set the user field in UserProfile
            profile_data['identity_sexuality'] = identity_sexuality_to_set  # set the user field in UserProfile
            profile_data['identity_gender'] = identity_gender_to_set
            profile_data['identity_ethic'] = identity_ethic_to_set
            profile_data['identity_pronouns'] = identity_pronouns_to_set
            profile_serializer = UserProfileSerializer(data=profile_data)
            profile_serializer.is_valid(raise_exception=True)
            profile = profile_serializer.save()

            if user_data['is_mentee'] or user_data['is_mentee']:
                MentorshipProgramProfile.objects.create(
                    user=user
                )

            try:
                send_invite(request.user.email)

                return Response(
                    {'status': True, 'message': 'User, TalentProfile, and UserProfile created successfully!'},
                    status=status.HTTP_201_CREATED)
            except Exception as e:
                print(e)
                return Response({'status': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(e)
        return Response({'status': 'Error', 'error': 'An unexpected error occurred.'},
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
    company_details = next(iter(request.data.get('company_id', [])), False)

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
    talent_profile = user.user
    role_names = request.data.get('job_roles')

    roles_to_set = []  # This list will hold the role objects to be set to the TalentProfile
    for role_name in role_names:
        try:
            # Try to get the role by name, and if it doesn't exist, create it.
            role, created = Roles.objects.get_or_create(name=role_name)
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
            role = Department.objects.get(name=role_name)
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
            role = SexualIdentities.objects.get(identity=role_name)
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
            role = GenderIdentities.objects.get(gender=role_name)
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
            role = EthicIdentities.objects.get(ethnicity=role_name)
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
    userprofile.save()

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

            # Set secure cookie
            # print(token)
            # response.set_cookie('auth_token', token)  # httponly=True to prevent access by JavaScript
            # response.set_cookie('auth_token', token, secure=False,
            #                     httponly=False)  # httponly=True to prevent access by JavaScript
            response = JsonResponse({'status': True, 'message': 'User created successfully', 'token': token},
                                    status=201)
            return response
        except Exception as e:
            # Log the exception for debugging
            print("Error while saving user: ", str(e))
            return JsonResponse({'status': False, 'error': 'Unable to create user'}, status=500)

    else:
        return JsonResponse({'status': False, 'error': 'Invalid request method'}, status=405)
