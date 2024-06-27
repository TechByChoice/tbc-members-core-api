import os
import logging
import json

import requests
from django.db.models import Q, Count
from django.core.cache import cache

from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from utils.emails import send_dynamic_email
from utils.helper import paginate_items, CustomPagination
from utils.slack import post_message
from .models import CompanyProfile, Department, Skill, Job
from .serializers import JobReferralSerializer, JobSerializer
from rest_framework.decorators import action

from ..core.serializers_member import TalentProfileSerializer
from ..member.models import MemberProfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class JobPagination(PageNumberPagination):
    page_size = 10  # Set default page display
    page_size_query_param = 'page_size'
    max_page_size = 100


class JobViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"], url_path="create-referral")
    def create_job_referral(self, request):
        data = request.data

        # find the company
        if "company_id" in data:
            company_id = data["company_id"]
        else:
            new_unclaimed_company = CompanyProfile.objects.create(
                company_name=data["company_name"],
                company_url=data["company_url"],
                unclaimed_account_creator=request.user,
                is_unclaimed_account=True,
                account_creator=request.user,
            )
            new_unclaimed_company.current_employees.add(request.user)
            new_unclaimed_company.referral_employees.add(request.user)
            new_unclaimed_company.save()
            company_id = new_unclaimed_company.id

        # Extract IDs for Many-to-Many relationships
        department_ids = [dept["id"] for dept in data.pop("department", [])]
        skill_ids = [skill["id"] for skill in data.pop("skills", [])]
        role_id = data.pop("role", [{}])[0].get("id")  # Assuming single role

        # Extract IDs for Foreign Key relationships
        min_compensation = data.pop("min_compensation", [{}])
        min_compensation_id = (
            min_compensation[0].get("id") if min_compensation is not None else None
        )

        max_compensation = data.pop("max_compensation", [{}])
        max_compensation_id = (
            max_compensation[0].get("id") if max_compensation is not None else None
        )

        # Update the data dictionary
        data["min_compensation"] = min_compensation_id
        data["max_compensation"] = max_compensation_id
        data["role"] = role_id
        data["department"] = department_ids
        data["skills"] = skill_ids
        data["parent_company"] = company_id
        data["status"] = "draft"
        data["is_referral_job"] = True
        data["created_by_id"] = request.user.id
        data["created_by"] = request.user.pk

        # Correct on_site_remote field
        if data["on_site_remote"] == "contract":
            data["on_site_remote"] = "CONTRACT"  # Replace with the correct choice

        # Handle years_of_experience field
        years_experience_value = data.pop("years_of_experience", [{}])[0].get("id")
        data["years_of_experience"] = years_experience_value

        # Serialize data
        serializer = JobReferralSerializer(data=data)
        if serializer.is_valid():
            job = serializer.save()

            # Set Many-to-Many relationships
            job.department.set(Department.objects.filter(id__in=department_ids))
            job.skills.set(Skill.objects.filter(id__in=skill_ids))

            # Set Foreign Key for company
            company_data = data.get("company")
            if company_data:
                company_id = company_data.get("id")
                company = CompanyProfile.objects.get(id=company_id)
                job.parent_company = company
                job.save()
            try:
                # Prepare email data
                email_data = {
                    "recipient_emails": [job.created_by.email],
                    "subject": "Your Job Referral is Now Published",
                    "template_id": "d-36a42b380265419f9263355d6eef9028",
                    "dynamic_template_data": {
                        "job_post_title": job.job_title,
                        "job_url": f'{os.environ["FRONTEND_URL"]}job/{job.id}',
                    },
                }
                send_dynamic_email(email_data)
                return Response(serializer.data, status=status.HTTP_200_CREATED)
            except BaseException as e:
                print(str(e))
                print("email not sent")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], url_path="referral/publish")
    def publish_referral_job(self, request, pk=None):
        """
        Mark job as pending by its ID.
        """
        try:
            job = Job.objects.get(pk=pk)
            job.status = "pending"
            job.save()
            serializer = JobSerializer(job)
            try:
                # Prepare email data
                email_data = {
                    "recipient_emails": [job.created_by.email],
                    "template_id": "d-4bf83b1cd93e4b5da4191c00982cf36e",
                    "dynamic_template_data": {
                        "job_post_title": job.job_title,
                        "job_url": f'{os.environ["FRONTEND_URL"]}job/{job.id}',
                    },
                }
                send_dynamic_email(email_data)

            except BaseException as e:
                print(str(e))
                print("email not sent")
            try:
                msg = (
                    f":rotating_light: *New Job Posted* :rotating_light:\n\n"
                    f"You have 3 business days to approve or reject {job.parent_company.company_name} post.\n\n"
                    f'Use this link to view the job post: [Job Link]({os.environ["FRONTEND_URL"] + "job/" + str(job.id)})'
                )

                post_message("C06BPP4BXFW", msg)
            except BaseException as e:
                print(str(e))
                print("Slack message (New job alert) not sent")
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=["get"], url_path="referral/active")
    def activate_referral_job(self, request, pk=None):
        """
        Mark job as active by its ID.
        """
        try:
            job = Job.objects.get(pk=pk)
            job.status = "active"
            job.save()
            serializer = JobSerializer(job)
            try:
                # Prepare email data
                email_data = {
                    "recipient_emails": [job.created_by.email],
                    "template_id": "d-4bf83b1cd93e4b5da4191c00982cf36e",
                    "dynamic_template_data": {
                        "job_post_title": job.job_title,
                        "job_url": f'{os.environ["FRONTEND_URL"]}job/{job.id}',
                    },
                }
                send_dynamic_email(email_data)
                return Response(serializer.data, status=status.HTTP_200_CREATED)
            except BaseException as e:
                print(str(e))
                print("email not sent")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=["get"], url_path="referral/pause")
    def pause_referral_job(self, request, pk=None):
        """
        Mark job as pending by its ID.
        """
        try:
            job = Job.objects.get(pk=pk)
            job.status = "pause"
            job.save()
            serializer = JobSerializer(job)
            try:
                # Prepare email data
                email_data = {
                    "recipient_emails": [job.created_by.email],
                    "template_id": "d-41ffeaa4c41248bd95d36d769687f261",
                    "dynamic_template_data": {
                        "job_post_title": job.job_title,
                        "job_url": f'{os.environ["FRONTEND_URL"]}job/{job.id}',
                    },
                }
                send_dynamic_email(email_data)
                return Response(serializer.data, status=status.HTTP_200_CREATED)
            except BaseException as e:
                print(str(e))
                print("email not sent")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=["get"], url_path="referral/closed")
    def closed_referral_job(self, request, pk=None):
        """
        Mark job as pending by its ID.
        """
        try:
            job = Job.objects.get(pk=pk)
            job.status = "closed"
            job.save()
            serializer = JobSerializer(job)
            try:
                # Prepare email data
                email_data = {
                    "recipient_emails": [job.created_by.email],
                    "template_id": "d-4bf83b1cd93e4b5da4191c00982cf36e",
                    "dynamic_template_data": {
                        "job_post_title": job.job_title,
                        "job_url": f'{os.environ["FRONTEND_URL"]}job/{job.id}',
                    },
                }
                send_dynamic_email(email_data)
                return Response(serializer.data, status=status.HTTP_200_CREATED)
            except BaseException as e:
                print(str(e))
                print("email not sent")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=["get"], url_path="get-job")
    def get_job(self, request, pk=None):
        """
        Retrieve a job by its ID.
        """
        try:
            job = Job.objects.get(pk=pk)
            serializer = JobSerializer(job)
            return Response(serializer.data)
        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["get"], url_path="all-jobs")
    def get_all_jobs(self, request):
        """
        Retrieve all job postings base on user profile

        """
        logger.info("Starting get_all_jobs function")

        url = f"{os.getenv('IT_API_URL')}api/v1/matches/jobs/"
        header_token = request.headers.get("Authorization", None)

        try:
            user_profile = MemberProfile.objects.get(user=request.user.id)
            logger.info(f"Retrieved user profile for user ID: {request.user.id}")
        except MemberProfile.DoesNotExist:
            logger.error(f"User profile not found for user ID: {request.user.id}")
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = TalentProfileSerializer(user_profile)

        user_posted_jobs = Job.objects.filter(created_by=request.user)
        user_posted_jobs_serializer = JobSerializer(user_posted_jobs, many=True)

        data_dump = {
            "user_profile": serializer.data,
            "department": serializer.data["department"],
            "user_role": serializer.data["role"],
            "user_level": serializer.data["tech_journey"],
            "user_skills": serializer.data["skills"],
            "header_token": header_token,
        }

        try:
            logger.info(f"Sending POST request to {url}")
            response = requests.post(
                url,
                data=json.dumps(data_dump),
                headers={'Content-Type': 'application/json'},
            )
            response.raise_for_status()  # Raises an HTTPError for bad responses

            response_json = response.json()
            logger.info(f"Received response with {len(response_json)} jobs")

            if len(response_json) > 0:
                data = {
                    "all_jobs": response_json,
                    "posted_jobs": []
                }
                return Response(data)
            else:
                data = {
                    "all_jobs": False,
                    "message": "We currently don't have any jobs that match your profile at this time",
                    "posted_jobs": []
                }
                return Response(data)

        except requests.exceptions.RequestException as error:
            logger.error(f"Error in API request: {error}")
            return Response({"message": "API request error"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="pull-jobs")
    def pull_all_job(self, request):
        logger.info("Starting pull_all_job function")

        cache_key = "all_active_jobs"
        cached_jobs = cache.get(cache_key)

        if cached_jobs is not None:
            logger.info("Returning cached jobs")
            return Response(cached_jobs, status=status.HTTP_200_OK)

        logger.info("Cache miss. Fetching active jobs from database")
        all_active_jobs = Job.objects.filter(status="active").only(
            "id", "parent_company", "role", "department", "min_compensation", "max_compensation", "location"
        )

        jobs = []
        chunk_size = 100
        total_jobs = all_active_jobs.count()
        logger.info(f"Processing {total_jobs} active jobs in chunks of {chunk_size}")

        for i in range(0, total_jobs, chunk_size):
            chunk = all_active_jobs[i:i + chunk_size]
            serializer = JobSerializer(chunk, many=True)
            jobs.extend(serializer.data)
            logger.info(f"Processed {min(i + chunk_size, total_jobs)} out of {total_jobs} jobs")

        logger.info(f"Caching {len(jobs)} jobs for 1 month")
        cache.set(cache_key, jobs, timeout=2592000)  # Cache for 1 month

        return Response(jobs, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="job-match")
    def get_top_job_match(self, request):
        """
        Retrieve top job postings.
        """
        talent_profile = MemberProfile.objects.get(user=request.user.id)

        # Extract skills, roles, and departments
        talent_skills = talent_profile.skills.all()
        talent_roles = talent_profile.role.all()
        talent_departments = talent_profile.department.all()

        # Create separate Q objects for each criteria
        skills_query = Q(skills__in=talent_skills)
        roles_query = Q(role__in=talent_roles)
        departments_query = Q(department__in=talent_departments)

        # Combine queries using OR logic
        combined_query = skills_query | roles_query | departments_query

        # Filter Job instances based on the combined query
        matching_jobs = Job.objects.filter(combined_query).distinct()

        # Annotate each job with a score based on the number of matching criteria
        matching_jobs = matching_jobs.annotate(
            score=Count(
                "skills",
                filter=Q(skills__in=talent_skills.values_list("id", flat=True)),
            )
                  + Count(
                "role",
                filter=Q(role__in=talent_profile.role.values_list("id", flat=True)),
            )
                  + Count(
                "department",
                filter=Q(
                    department__in=talent_departments.values_list("id", flat=True)
                ),
            )
        ).order_by("-score")

        matching_jobs_serialized = JobSerializer(matching_jobs, many=True).data

        # Render the results in a template
        return Response(
            {"status": True, "matching_jobs": matching_jobs_serialized},
            status=status.HTTP_200_OK,
        )
