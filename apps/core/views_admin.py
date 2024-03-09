from django.db.models import Count
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import CustomUser, SexualIdentities, GenderIdentities, EthicIdentities, PronounsIdentities
from ..company.models import Department, Roles, Industries, Skill, CompanyProfile
from ..member.models import MemberProfile
from ..mentorship.models import MentorProfile


class CombinedBreakdownView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        # Aggregate MemberProfile by tech_journey
        tech_journey_counts = MemberProfile.objects.values('tech_journey').annotate(
            count=Count('tech_journey')).order_by('tech_journey')
        # Map codes to labels
        for item in tech_journey_counts:
            item['name'] = dict(MemberProfile.CAREER_JOURNEY).get(item['tech_journey'], 'Unknown')

        response_data = {
            'skills': list(
                Skill.objects.annotate(members_count=Count('talent_skills_list')).filter(members_count__gt=0).order_by(
                    '-members_count').values('name', 'members_count')),
            'departments': list(Department.objects.annotate(members_count=Count('talent_department_list')).filter(
                members_count__gt=0).order_by('-members_count').values('name', 'members_count')),
            'roles': list(
                Roles.objects.annotate(members_count=Count('talent_role_types')).filter(members_count__gt=0).order_by(
                    '-members_count').values('name', 'members_count')),
            'industries': list(Industries.objects.annotate(members_count=Count('member_industries')).filter(
                members_count__gt=0).order_by('-members_count').values('name', 'members_count')),
            'identity_sexuality': list(
                SexualIdentities.objects.annotate(members_count=Count('userprofile_identity_sexuality')).filter(
                    members_count__gt=0).order_by('-members_count').values('name', 'members_count')),
            'identity_gender': list(
                GenderIdentities.objects.annotate(members_count=Count('userprofile_identity_gender')).filter(
                    members_count__gt=0).order_by('-members_count').values('name', 'members_count')),
            'identity_ethic': list(
                EthicIdentities.objects.annotate(members_count=Count('userprofile_identity_ethic')).filter(
                    members_count__gt=0).order_by('-members_count').values('name', 'members_count')),
            'identity_pronouns': list(
                PronounsIdentities.objects.annotate(members_count=Count('userprofile_identity_pronouns')).filter(
                    members_count__gt=0).order_by('-members_count').values('name', 'members_count')),
            'total_member': CustomUser.objects.filter(is_member=True).count(),
            'total_member_level': tech_journey_counts,
            'total_member_talent_choice': CustomUser.objects.filter(is_talent_choice=True).count(),
            'talent_choice_job_roles_needed': list(
                Roles.objects.filter(
                    talent_role_types__user__is_talent_choice=True
                ).annotate(members_count=Count('talent_role_types')).filter(members_count__gt=0).order_by(
                    '-members_count').values('name', 'members_count')),
            'total_company_talent_choice': CompanyProfile.objects.filter(talent_choice_account=True).count(),
            'total_active_mentors': MentorProfile.objects.filter(mentor_status__exact="active").count(),
            'total_mentors_applications': MentorProfile.objects.filter(mentor_status__exact="submitted").count(),
            'total_mentors_interviewing': MentorProfile.objects.filter(mentor_status__exact="interviewing").count(),
            'total_mentors_need_cal_info': MentorProfile.objects.filter(mentor_status__exact="need_cal_info").count(),
        }

        # DEI Categories might require custom handling, you may need to adjust the function or directly query here

        return Response(response_data)


def get_aggregated_data(model, related_name=None):
    if related_name:
        return model.objects.annotate(user_count=Count(related_name)).all()
    else:
        # For models without a direct relation, adjust accordingly
        return model.objects.all()
