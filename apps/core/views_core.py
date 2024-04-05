from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.company.models import (
    Roles,
    CompanyProfile,
    CAREER_JOURNEY,
    Skill,
    Department,
    Industries,
    CompanyTypes,
    SalaryRange, COMPANY_SIZE, ON_SITE_REMOTE,
)
from apps.core.models import (
    PronounsIdentities,
    GenderIdentities,
    SexualIdentities,
    EthicIdentities,
    CommunityNeeds,
    UserProfile,
)
from apps.core.serializers_member import TalentProfileSerializer, FullTalentProfileSerializer
from apps.member.models import MemberProfile
from utils.helper import CustomPagination, paginate_items


@api_view(["GET"])
def get_dropdown_data(request):
    data = {}
    requested_fields = request.query_params.getlist("fields", [])

    if not requested_fields or "pronouns" in requested_fields:
        data["pronouns"] = list(PronounsIdentities.objects.values("name", "id"))

    if not requested_fields or "job_roles" in requested_fields:
        data["job_roles"] = list(Roles.objects.order_by("name").values("name", "id"))

    if not requested_fields or "years_of_experience" in requested_fields:
        data["years_of_experience"] = [
            {"value": code, "label": description}
            for code, description in CAREER_JOURNEY
        ]

    if not requested_fields or "companies" in requested_fields:
        data["companies"] = list(
            CompanyProfile.objects.order_by("company_name").values(
                "company_name", "id", "logo", "company_url"
            )
        )

    if not requested_fields or "job_skills" in requested_fields:
        data["job_skills"] = list(Skill.objects.order_by("name").values("name", "id"))

    if not requested_fields or "job_departments" in requested_fields:
        data["job_departments"] = list(
            Department.objects.order_by("name").values("name", "id")
        )

    if not requested_fields or "job_industries" in requested_fields:
        data["job_industries"] = list(
            Industries.objects.order_by("name").values("name", "id")
        )

    if not requested_fields or "company_types" in requested_fields:
        data["company_types"] = list(
            CompanyTypes.objects.order_by("name").values("name", "id")
        )

    if not requested_fields or "gender" in requested_fields:
        data["gender"] = list(
            GenderIdentities.objects.order_by("name").values("name", "id")
        )

    if not requested_fields or "sexuality" in requested_fields:
        data["sexuality"] = list(
            SexualIdentities.objects.order_by("name").values("name", "id")
        )

    if not requested_fields or "ethic" in requested_fields:
        data["ethic"] = list(
            EthicIdentities.objects.order_by("name").values("name", "id")
        )

    if not requested_fields or "job_salary_range" in requested_fields:
        data["job_salary_range"] = list(SalaryRange.objects.values("range", "id"))

    if not requested_fields or "community_needs" in requested_fields:
        data["community_needs"] = list(CommunityNeeds.objects.values("name", "id"))

    if not requested_fields or "how_connected" in requested_fields:
        data["how_connected"] = UserProfile.HOW_CONNECTION_MADE

    if not requested_fields or "company_size" in requested_fields:
        data["company_size"] = COMPANY_SIZE

    if not requested_fields or "on_site_remote" in requested_fields:
        data["on_site_remote"] = ON_SITE_REMOTE

    data["status"] = True

    return Response(data)


@api_view(["GET"])
def get_all_members(request):
    data = {}

    # Initialize the paginator
    paginator = CustomPagination()

    requested_fields = request.query_params.getlist("fields", [])

    members = MemberProfile.objects.filter(user__is_active=True).order_by("created_at")
    paginated_members = paginate_items(members, request, paginator, FullTalentProfileSerializer)

    data["members"] = paginated_members
    data["status"] = True

    return Response(data)


