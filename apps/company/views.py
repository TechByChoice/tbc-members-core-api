from datetime import datetime

from django.http import HttpResponseBadRequest
from django.shortcuts import render
import requests
from xml.etree import ElementTree as ET

from rest_framework import status, generics
from rest_framework.response import Response

from apps.company.models import Job, Roles, Department, CompanyProfile
from apps.company.serializers import APIKeySerializer
from apps.core.models import CustomUser


GREENHOUSE_API_URL = "https://harvest.greenhouse.io/v1/jobs"
GREENHOUSE_CANDIDATES_URL = "https://harvest.greenhouse.io/v1/candidates"


def normalize_string(s):
    """Normalize string: Lowercase and remove non-alphanumeric characters."""
    return "".join(filter(str.isalnum, s)).lower()


def get_closest_match(commitment):
    JOB_TYPE_CHOICE = (
        ("full time", "full time"),
        ("part time", "part time"),
        ("contracting", "contracting"),
        ("volunteer", "volunteer"),
        ("temporary", "temporary"),
        ("internship", "internship"),
        ("apprenticeship", "apprenticeship"),
    )
    normalized_commitment = normalize_string(commitment)
    for choice in JOB_TYPE_CHOICE:
        if normalize_string(
            choice[1]
        ) in normalized_commitment or normalized_commitment in normalize_string(
            choice[1]
        ):
            return choice[1]
    return None


def sync_jobs_from_lever(company):
    if not company.lever_xml_feed_url:
        return

    response = requests.get(company.lever_xml_feed_url)
    tree = ET.ElementTree(ET.fromstring(response.content))

    for job in tree.findall("job"):
        role_name = job.find("position").text
        department_name = job.find("category").text
        role_instance, _ = Roles.objects.get_or_create(name=role_name)
        department_instance, _ = Department.objects.get_or_create(name=department_name)
        user = CustomUser.objects.get(id=1)
        company_profile_instance, _ = (
            company_profile,
            created,
        ) = CompanyProfile.objects.get(company_name=job.find("employer").text)
        # Companies will have to create an account for this to work,
        # so we don't need to use get_or_create(), just get()
        # company_profile_instance, _ = company_profile, created = CompanyProfile.objects.get_or_create(
        #     account_creator=user,  # An instance of CustomUser
        #     unclaimed_account_creator=user,  # An instance of CustomUser
        #     is_unclaimed_account=False,
        #     company_name="Example Company",
        #     company_size="unknown",
        #     is_startup=False,
        #     confirm_service_agreement=True
        # )

        timestamp = int(job.find("post_date").text) / 1000  # Convert to seconds
        job_data = {
            "role": role_instance,  # this is our role
            "external_description": job.find("description").text,
            "url": job.find("apply_url").text,
            "location": job.find("location").text,
            "job_type": get_closest_match(job.find("commitment").text),
            "pub_date": datetime.fromtimestamp(timestamp),
            "parent_company": company_profile_instance,
            "lever_id": job.find("id").text,
        }

        # Use the Lever job ID as the unique identifier to avoid duplicates.
        job_instance, created = Job.objects.update_or_create(
            lever_id=job_data["lever_id"],
            status="pending",
            on_site_remote="unknown",
            defaults=job_data,
        )
        if created:
            job_instance.department.set([department_instance])
            # job_instance.role.set([role_instance])


def sync_jobs_from_workable():
    WORKABLE_API_ENDPOINT = "https://www.workable.com/api/{your_account_name}/jobs"
    response = requests.get(
        WORKABLE_API_ENDPOINT, headers={"Authorization": "Bearer YOUR_API_KEY"}
    )

    if response.status_code == 200:
        jobs = response.json()

        for job in jobs:
            # Map fields from Workable's job data to your Django model fields
            Job.objects.update_or_create(
                lever_id=job.get("id"),
                defaults={
                    "job_title": job.get("title"),
                    "description": job.get("description"),
                    # ... map other fields accordingly
                },
            )
    else:
        # Handle errors, logging, etc.
        print(f"Failed to fetch jobs. Status Code: {response.status_code}")


def sync_jobs_from_greenhouse(company):
    if not company.greenhouse_api_key:
        return

    headers = {"Authorization": f"Bearer {company.greenhouse_api_key}"}

    response = requests.get(GREENHOUSE_API_URL, headers=headers)
    jobs = response.json()

    for job in jobs:
        role_name = job["title"]
        department_name = job["department"]["name"]
        role_instance = ""
        department_instance = ""
        # ... same as before for creating role and department

        job_data = {
            # ... similar to before, but now fetching data from the Greenhouse JSON structure
            "role": role_instance,
            "external_description": job["content"],
            "url": job["absolute_url"],
            # ... more fields here
            "greenhouse_id": job["id"],
        }

        job_instance, created = Job.objects.update_or_create(
            greenhouse_id=job_data["greenhouse_id"], defaults=job_data
        )
        if created:
            job_instance.department.set([department_instance])


def submit_candidate_to_greenhouse(talent_profile, api_key):
    user = talent_profile.user

    # Step 1: Map the fields
    data = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        # More fields can be added based on the Greenhouse API documentation and your model's fields
        "applications": [
            {
                "job_id": "12345"  # This should be the actual job ID for which the talent is being submitted
            }
        ],
        # Attachments like resumes can also be sent, refer to Greenhouse documentation on how to send attachments
    }

    headers = {"Authorization": f"Bearer {api_key}"}

    # Step 2: Send the POST request
    try:
        response = requests.post(GREENHOUSE_CANDIDATES_URL, json=data, headers=headers)
        response.raise_for_status()  # This will raise an error if the request failed

        # Check if the candidate was successfully created
        if response.status_code == 201:
            return (
                response.json()
            )  # Return the response, which will typically include the candidate's new ID
        else:
            # Handle other unexpected statuses
            print(f"Unexpected status code: {response.status_code}")
            print(response.text)
            return None

    # Step 3: Implement error handling and logging
    except requests.RequestException as e:
        print(f"Error submitting candidate: {e}")
        return None


class AbstractSetAPIKey(generics.UpdateAPIView):
    queryset = CompanyProfile.objects.all()
    serializer_class = APIKeySerializer
    lookup_url_kwarg = "company_id"
    api_key_field = None  # Abstract attribute to be set in child classes

    def update(self, request, *args, **kwargs):
        if not self.api_key_field:
            return Response(
                {"detail": "API key field not set."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        company = self.get_object()

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            setattr(company, self.api_key_field, serializer.validated_data["api_key"])
            company.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
