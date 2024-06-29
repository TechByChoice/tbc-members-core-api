from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from apps.company.models import (
    Roles, CompanyProfile, CAREER_JOURNEY, Skill, Department, Industries,
    CompanyTypes, SalaryRange, COMPANY_SIZE, ON_SITE_REMOTE,
)
from apps.core.models import (
    PronounsIdentities, GenderIdentities, SexualIdentities, EthicIdentities,
    CommunityNeeds, UserProfile,
)
from utils.logging_helper import get_logger, log_exception, timed_function
from utils.cache_utils import cache_decorator
from utils.api_helpers import api_response

logger = get_logger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
@log_exception(logger)
@timed_function(logger)
@cache_decorator(timeout=3600)  # Cache for 1 hour
def get_dropdown_data(request):
    data = {}
    requested_fields = request.query_params.getlist("fields", [])

    field_mappings = {
        "pronouns": (PronounsIdentities, "name", "id"),
        "job_roles": (Roles, "name", "id"),
        "companies": (CompanyProfile, "company_name", "id", "logo", "company_url"),
        "job_skills": (Skill, "name", "id"),
        "job_departments": (Department, "name", "id"),
        "job_industries": (Industries, "name", "id"),
        "company_types": (CompanyTypes, "name", "id"),
        "gender": (GenderIdentities, "name", "id"),
        "sexuality": (SexualIdentities, "name", "id"),
        "ethic": (EthicIdentities, "name", "id"),
        "job_salary_range": (SalaryRange, "range", "id"),
        "community_needs": (CommunityNeeds, "name", "id"),
    }

    for field, model_info in field_mappings.items():
        if not requested_fields or field in requested_fields:
            model, *fields = model_info
            data[field] = list(model.objects.order_by(fields[0]).values(*fields))

    if not requested_fields or "years_of_experience" in requested_fields:
        data["years_of_experience"] = [
            {"value": code, "label": description}
            for code, description in CAREER_JOURNEY
        ]

    if not requested_fields or "how_connected" in requested_fields:
        data["how_connected"] = UserProfile.HOW_CONNECTION_MADE

    if not requested_fields or "company_size" in requested_fields:
        data["company_size"] = COMPANY_SIZE

    if not requested_fields or "on_site_remote" in requested_fields:
        data["on_site_remote"] = ON_SITE_REMOTE

    return api_response(data=data, message="Dropdown data retrieved successfully")
