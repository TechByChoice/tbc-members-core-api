from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.company.models import Roles, CompanyProfile, CAREER_JOURNEY, Skill, Department, Industries, CompanyTypes, \
    SalaryRange
from apps.core.models import PronounsIdentities, GenderIdentities, SexualIdentities, EthicIdentities


@api_view(['GET'])
def get_dropdown_data(request):
    data = {}
    requested_fields = request.query_params.getlist('fields', [])

    if not requested_fields or 'pronouns' in requested_fields:
        data['pronouns'] = list(PronounsIdentities.objects.values('pronouns', 'id'))

    if not requested_fields or 'job_roles' in requested_fields:
        data['job_roles'] = list(Roles.objects.values('name', 'id'))

    if not requested_fields or 'years_of_experience' in requested_fields:
        data['years_of_experience'] = [{'value': code, 'label': description} for code, description in CAREER_JOURNEY]

    if not requested_fields or 'companies' in requested_fields:
        data['companies'] = list(CompanyProfile.objects.values('company_name', 'id', 'logo', 'company_url'))

    if not requested_fields or 'job_skills' in requested_fields:
        data['job_skills'] = list(Skill.objects.values('name', 'id'))

    if not requested_fields or 'job_departments' in requested_fields:
        data['job_departments'] = list(Department.objects.values('name', 'id'))

    if not requested_fields or 'job_industries' in requested_fields:
        data['job_industries'] = list(Industries.objects.values('name', 'id'))

    if not requested_fields or 'company_types' in requested_fields:
        data['company_types'] = list(CompanyTypes.objects.values('name', 'id'))

    if not requested_fields or 'gender' in requested_fields:
        data['gender'] = list(GenderIdentities.objects.values('gender', 'id'))

    if not requested_fields or 'sexuality' in requested_fields:
        data['sexuality'] = list(SexualIdentities.objects.values('identity', 'id'))

    if not requested_fields or 'ethic' in requested_fields:
        data['ethic'] = list(EthicIdentities.objects.values('ethnicity', 'id'))

    if not requested_fields or 'job_salary_range' in requested_fields:
        data['job_salary_range'] = list(SalaryRange.objects.values('range', 'id'))

    data['status'] = True

    return Response(data)