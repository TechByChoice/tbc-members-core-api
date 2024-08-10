import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from knox.models import AuthToken
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.company.models import (
    Roles,
    CompanyProfile,
    CAREER_JOURNEY,
    Skill,
    Department,
    Industries,
    CompanyTypes,
    SalaryRange, COMPANY_SIZE, ON_SITE_REMOTE, Certs,
)
from apps.core.models import (
    PronounsIdentities,
    GenderIdentities,
    SexualIdentities,
    EthicIdentities,
    CommunityNeeds,
    UserProfile,
)
from apps.core.serializers_member import FullTalentProfileSerializer
from apps.member.models import MemberProfile
from utils.helper import CustomPagination, paginate_items

logger = logging.getLogger(__name__)

User = get_user_model()


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

    if not requested_fields or "certs" in requested_fields:
        data["certs"] = list(Certs.objects.order_by("name").values("name", "id"))

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


class VerifyAdminView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Verify if the user associated with the provided Knox token is authorized and an admin.

        This endpoint checks the validity of the provided Knox token, verifies if the associated
        user exists and is an admin. It uses caching to improve performance for repeated
        requests with the same token.

        Args:
            request (Request): The request object containing the Authorization header.

        Returns:
            Response: A JSON response indicating whether the user is an authorized admin.

        Raises:
            AuthToken.DoesNotExist: If the provided token is invalid or expired.
        """
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            logger.warning("Missing Authorization header in verify-admin request")
            return Response({"is_admin": False, "error": "Missing Authorization header"},
                            status=status.HTTP_401_UNAUTHORIZED)

        try:
            # Extract the token from the Authorization header
            token = auth_header.split()[1]

            # Check cache first
            # cache_key = f"admin_status_{token}"
            # cached_result = cache.get(cache_key)
            # if cached_result is not None:
            #     return Response({"is_admin": cached_result}, status=status.HTTP_200_OK)

            # Verify the Knox token
            token_obj = AuthToken.objects.get(token_key=token[:8])
            if not token_obj.user.is_authenticated:
                raise AuthToken.DoesNotExist

            # Get the user and check if they are an admin
            user = token_obj.user
            is_admin = user.is_staff and user.is_active

            # Cache the result
            # cache_timeout = getattr(settings, 'KNOX_TOKEN_TTL', 60 * 10).total_seconds()
            # cache.set(cache_key, is_admin, int(cache_timeout))

            logger.info(f"User {user.id} admin status verified: {is_admin}")
            return Response({"is_admin": is_admin}, status=status.HTTP_200_OK)

        except AuthToken.DoesNotExist:
            logger.warning(f"Invalid or expired token in verify-admin request")
            return Response({"is_admin": False, "error": "Invalid or expired token"},
                            status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            logger.warning(f"User not found for token in verify-admin request")
            return Response({"is_admin": False, "error": "User not found"},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error in verify-admin request: {str(e)}")
            return Response({"is_admin": False, "error": "An unexpected error occurred"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
