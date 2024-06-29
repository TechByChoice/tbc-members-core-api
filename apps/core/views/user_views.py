from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.serializers.user_serializers import CustomUserSerializer
from apps.core.serializers.profile_serializers import UserProfileSerializer
from utils.logging_helper import get_logger, log_exception, timed_function
from utils.cache_utils import cache_decorator
from utils.api_helpers import api_response
from utils.profile_utils import get_user_profile, update_user_profile

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
        profile_data = UserProfileSerializer(user_profile).data

        response_data = {
            "user_info": user_data,
            "profile_info": profile_data,
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
