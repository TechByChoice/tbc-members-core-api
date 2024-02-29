import logging

import requests
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from apps.company.models import CompanyProfile
from apps.company.serializers import CompanyProfileSerializer

logger = logging.getLogger(__name__)

REVIEWS_URL = 'http://127.0.0.1:7000/'


class CompanyView(APIView):

    def get(self, request, pk=None):
        """
        This view returns a single company profile
        identified by the `company_id` passed in the URL.
        """
        company_data = CompanyProfile.objects.get(id=pk)
        serializer_data = CompanyProfileSerializer(company_data)
        # get company review
        # headers = {"Authorization": f"Bearer {request.user.token}"}

        try:
            response = requests.get(f'http://127.0.0.1:7000/api/reviews/company/{pk}/', verify=False)
            jobs = response.json()
            return Response(
                {"status": True, "company": serializer_data.data, "companyReivew": jobs}, status=status.HTTP_200_OK
            )
        except Exception as e:
            print(f'error: {e}')
            return Response(
                {"status": False, "error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
