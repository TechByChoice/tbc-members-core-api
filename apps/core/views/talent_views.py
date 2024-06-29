from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.serializers.talent_serializers import FullTalentProfileSerializer
from apps.member.models import MemberProfile
from utils.logging_helper import get_logger, log_exception, timed_function
from utils.helper import CustomPagination, paginate_items
from utils.api_helpers import api_response

logger = get_logger(__name__)


class TalentListView(APIView):
    permission_classes = [IsAuthenticated]

    @log_exception(logger)
    @timed_function(logger)
    def get(self, request):
        paginator = CustomPagination()
        members = MemberProfile.objects.filter(user__is_active=True).order_by("created_at")
        paginated_members = paginate_items(members, request, paginator, FullTalentProfileSerializer)

        return api_response(data={"members": paginated_members}, message="All members retrieved successfully")


class TalentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @log_exception(logger)
    @timed_function(logger)
    def get(self, request, pk):
        try:
            member = MemberProfile.objects.get(pk=pk, user__is_active=True)
            serializer = FullTalentProfileSerializer(member)
            return api_response(data=serializer.data, message="Member details retrieved successfully")
        except MemberProfile.DoesNotExist:
            return api_response(message="Member not found", status_code=404)
