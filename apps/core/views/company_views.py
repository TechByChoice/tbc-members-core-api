from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ViewSet

from apps.company.models import CompanyProfile
from apps.core.serializers.company_serializers import CompanyProfileSerializer
from utils.logging_helper import get_logger, log_exception, timed_function
from utils.api_helpers import api_response
from utils.helper import prepend_https_if_not_empty

logger = get_logger(__name__)


class CompanyViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @log_exception(logger)
    @timed_function(logger)
    @action(detail=False, methods=['post'], url_path='create-onboarding')
    def create_onboarding(self, request):
        user = request.user
        company_data = {
            'company_name': request.data.get('company_name'),
            'company_url': prepend_https_if_not_empty(request.data.get('website', '')),
            'linkedin': prepend_https_if_not_empty(request.data.get('linkedin', '')),
            'twitter': prepend_https_if_not_empty(request.data.get('twitter', '')),
            'youtube': prepend_https_if_not_empty(request.data.get('youtube', '')),
            'facebook': prepend_https_if_not_empty(request.data.get('facebook', '')),
            'instagram': prepend_https_if_not_empty(request.data.get('instagram', '')),
            'location': request.data.get('location', ''),
            'city': request.data.get('city', ''),
            'state': request.data.get('state', ''),
            'postal_code': request.data.get('postalCode', ''),
            'mission': request.data.get('mission'),
            'company_size': request.data.get('company_size'),
        }

        serializer = CompanyProfileSerializer(data=company_data, context={'request': request})
        if serializer.is_valid():
            company = serializer.save()
            if 'logo' in request.FILES:
                company.logo = request.FILES['logo']
                company.save()
            return api_response(data={"companyId": company.id}, message="Company profile created successfully",
                                status_code=201)
        else:
            return api_response(errors=serializer.errors, message="Failed to create company profile", status_code=400)
