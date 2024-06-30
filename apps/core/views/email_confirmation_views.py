from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from knox.models import AuthToken
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from apps.core.models import CustomUser
from utils.logging_helper import get_logger, log_exception, timed_function
from utils.api_helpers import api_response

logger = get_logger(__name__)


class ConfirmEmailAPIView(APIView):
    permission_classes = [AllowAny]

    @log_exception(logger)
    @timed_function(logger)
    def get(self, request, id=None, token=None):
        try:
            uid = force_str(urlsafe_base64_decode(id))
            user = CustomUser.objects.get(id=uid)

            if user.is_email_confirmed:
                return api_response(message="Email already confirmed!")

            is_token_valid = default_token_generator.check_token(user, token)

            if is_token_valid:
                user.is_active = True
                user.is_email_confirmed = True
                user.save()
                _, token = AuthToken.objects.create(user)
                return api_response(data={"token": token}, message="Email confirmed! Please complete your account.")
            else:
                return api_response(message="Invalid email token. Please contact support.",
                                    status_code=status.HTTP_400_BAD_REQUEST)

        except CustomUser.DoesNotExist:
            logger.warning(f"User does not exist for id: {id}")
            return api_response(message="Invalid email token or user does not exist.",
                                status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unhandled error: {e}")
            return api_response(message="An unexpected error occurred.",
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
