from django.db.models import Q, Count

from rest_framework import viewsets, status
from rest_framework.response import Response

from .models import CompanyProfile, Industries, Department, Skill, Roles, Job
from .serializers import CompanySignUpSerializer, CompanyOpenRolesSerializer, JobReferralSerializer, JobSerializer
from rest_framework.decorators import action

from ..talent.models import TalentProfile


class JobViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'], url_path='create-referral')
    def create_job_referral(self, request):
        data = request.data

        # find the company
        company_id = data['company_id']

        # Extract IDs for Many-to-Many relationships
        department_ids = [dept['id'] for dept in data.pop('department', [])]
        skill_ids = [skill['id'] for skill in data.pop('skills', [])]
        role_id = data.pop('role', [{}])[0].get('id')  # Assuming single role

        # Extract IDs for Foreign Key relationships
        min_compensation_id = data.pop('min_compensation', [{}])[0].get('id')
        max_compensation_id = data.pop('max_compensation', [{}])[0].get('id')

        # Update the data dictionary
        data['min_compensation'] = min_compensation_id
        data['max_compensation'] = max_compensation_id
        data['role'] = role_id
        data['department'] = department_ids
        data['skills'] = skill_ids
        data['parent_company'] = company_id
        data['status'] = 'draft'
        data['is_referral_job'] = True
        data['created_by_id'] = request.user.id
        data['created_by'] = request.user.id

        # Correct on_site_remote field
        if data['on_site_remote'] == 'contract':
            data['on_site_remote'] = 'CONTRACT'  # Replace with the correct choice

        # Handle years_of_experience field
        years_experience_value = data.pop('years_of_experience', [{}])[0].get('id')
        data['years_of_experience'] = years_experience_value

        # Serialize data
        serializer = JobReferralSerializer(data=data)
        if serializer.is_valid():
            job = serializer.save()

            # Set Many-to-Many relationships
            job.department.set(Department.objects.filter(id__in=department_ids))
            job.skills.set(Skill.objects.filter(id__in=skill_ids))

            # Set Foreign Key for company
            company_data = data.get('company')
            if company_data:
                company_id = company_data.get('id')
                company = CompanyProfile.objects.get(id=company_id)
                job.parent_company = company
                job.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='get-job')
    def get_job(self, request, pk=None):
        """
        Retrieve a job by its ID.
        """
        try:
            job = Job.objects.get(pk=pk)
            serializer = JobSerializer(job)
            return Response(serializer.data)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='referral/publish')
    def publish_referral_job(self, request, pk=None):
        """
        Mark job as pending by its ID.
        """
        try:
            job = Job.objects.get(pk=pk)
            job.status = 'pending'
            job.save()
            serializer = JobSerializer(job)
            return Response(serializer.data)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='referral/active')
    def activate_referral_job(self, request, pk=None):
        """
        Mark job as pending by its ID.
        """
        try:
            job = Job.objects.get(pk=pk)
            job.status = 'active'
            job.save()
            serializer = JobSerializer(job)
            return Response(serializer.data)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='referral/pause')
    def pause_referral_job(self, request, pk=None):
        """
        Mark job as pending by its ID.
        """
        print(request.user)
        try:
            job = Job.objects.get(pk=pk)
            job.status = 'pause'
            job.save()
            serializer = JobSerializer(job)
            return Response(serializer.data)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='referral/closed')
    def closed_referral_job(self, request, pk=None):
        """
        Mark job as pending by its ID.
        """
        print(request.user)
        try:
            job = Job.objects.get(pk=pk)
            job.status = 'closed'
            job.save()
            serializer = JobSerializer(job)
            return Response(serializer.data)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='all-jobs')
    def get_all_jobs(self, request):
        """
        Retrieve all job postings.
        """
        all_active_jobs = Job.objects.filter(status='active')
        posted_job = Job.objects.filter(created_by=request.user.id)

        all_active_jobs_serializer = JobSerializer(all_active_jobs, many=True)
        posted_job_serializer = JobSerializer(posted_job, many=True)
        data = {
            'all_jobs': all_active_jobs_serializer.data,
            'posted_job': posted_job_serializer.data
        }
        return Response(data)

    @action(detail=False, methods=['get'], url_path='job-match')
    def get_top_job_match(self, request):
        """
        Retrieve top job postings.
        """
        talent_profile = TalentProfile.objects.get(user=request.user.id)

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
            score=Count('skills', filter=Q(skills__in=talent_skills.values_list('id', flat=True))) +
                  Count('role', filter=Q(role__in=talent_profile.role.values_list('id', flat=True))) +
                  Count('department', filter=Q(department__in=talent_departments.values_list('id', flat=True)))
        ).order_by('-score')

        matching_jobs_serialized = JobSerializer(matching_jobs, many=True).data

        # Render the results in a template
        return Response({'status': True, 'matching_jobs': matching_jobs_serialized}, status=status.HTTP_200_OK)