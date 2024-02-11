from rest_framework.response import Response
from rest_framework import status
from django.views import View
from rest_framework.decorators import action

from apps.company.models import Job, CompanyProfile, Skill, Roles
from apps.talent.models import TalentProfile


class JobMatchView(View):
    def get(self, request, *args, **kwargs):
        # Get the TalentProfile instance
        print(f"Headers: {request.headers}")
        talent_profile = TalentProfile.objects.get(user=request.user.id)

        # Extract skills, roles, and departments
        talent_skills = talent_profile.skills.all()
        talent_roles = talent_profile.role.all()
        talent_departments = talent_profile.department.all()

        # Filter Job instances based on the TalentProfile's preferences
        matching_jobs = Job.objects.filter(
            skills__in=talent_skills,
            role__in=talent_roles,
            department__in=talent_departments,
        ).distinct()

        return Response(
            {"status": True, "jobs": matching_jobs}, status=status.HTTP_200_OK
        )
