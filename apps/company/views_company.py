import logging

import requests
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from apps.company.models import CompanyProfile, Job
from apps.company.serializers import CompanyProfileSerializer, JobSerializer, JobSimpleSerializer

logger = logging.getLogger(__name__)

REVIEWS_URL = 'http://127.0.0.1:7000/'


class CompanyView(APIView):

    def get(self, request, pk=None):
        """
        This view returns a single company profile
        identified by the `company_id` passed in the URL.
        """
        talent_choice_jobs = {}
        try:
            company_data = CompanyProfile.objects.get(id=pk)

        except CompanyProfile.DoesNotExist:
            return Response(
                {"status": False, "error": "Company not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer_data = CompanyProfileSerializer(company_data).data
        job_list = Job.objects.filter(parent_company=pk, status="active")
        serializer_job_list = JobSimpleSerializer(job_list, many=True).data
        # Make an external request to get company reviews
        try:
            response = requests.get(f'http://127.0.0.1:7000/api/reviews/company/{pk}/', verify=False)
            response.raise_for_status()
            reviews = response.json()
        except requests.exceptions.HTTPError as http_err:
            return Response(
                {"status": False, "error": f"HTTP error occurred: {http_err}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {"status": False, "error": f"An unexpected error occurred: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        # Make an external request to get talent choice data
        if company_data.talent_choice_account:
            try:
                response = requests.get(f'http://127.0.0.1:8001/core/api/company/details/?company_id={pk}', verify=False)
                response.raise_for_status()
                talent_choice_jobs = response.json()
            except requests.exceptions.HTTPError as http_err:
                return Response(
                    {"status": False, "error": f"HTTP error occurred: {http_err}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            except Exception as e:
                return Response(
                    {"status": False, "error": f"An unexpected error occurred: {e}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # Return response with company profile data and reviews
        return Response(
            {
                "status": True,
                "company": serializer_data,
                "companyJobs": serializer_job_list,
                "companyReview": reviews,
                "talentChoice": talent_choice_jobs
            },
            status=status.HTTP_200_OK
        )
