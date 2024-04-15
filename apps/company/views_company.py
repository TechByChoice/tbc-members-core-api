import logging
import os

import requests
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ViewSet

from apps.company.filters import CompanyProfileFilter
from apps.company.models import CompanyProfile, Job
from apps.company.serializers import CompanyProfileSerializer, JobSimpleSerializer

logger = logging.getLogger(__name__)

REVIEWS_URL = 'http://127.0.0.1:7000/'


class CompanyView(ViewSet):

    def retrieve(self, request, pk=None):
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
                response = requests.get(f'{os.environ["TC_API_URL"]}core/api/company/details/?company_id={pk}', verify=False)
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


    def list(self, request):
        """
        This view returns a paginated and filterable list of all company profiles.
        """
        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get('page_size', 10)
        paginator.page_size_query_param = 'page_size'

        try:
            company_data = CompanyProfile.objects.all()
            filter_backends = (DjangoFilterBackend,)
            filterset_class = CompanyProfileFilter

            if company_data.exists():
                filtered_data = filterset_class(request.GET, queryset=company_data)
                if not filtered_data.qs.exists():
                    return Response({"status": False, "error": "No companies found matching the filter."},
                                    status=status.HTTP_404_NOT_FOUND)

                result_page = paginator.paginate_queryset(filtered_data.qs, request)
                serializer = CompanyProfileSerializer(result_page, many=True, context={'request': request})
                return paginator.get_paginated_response(serializer.data)
            else:
                return Response({"status": False, "error": "No companies found."},
                                status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return Response({"status": False, "error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)