from django.db.models import Count
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from apps.core.models import CustomUser, SexualIdentities, GenderIdentities, EthicIdentities, PronounsIdentities
from apps.company.models import Department, Roles, Industries, Skill, CompanyProfile
from apps.member.models import MemberProfile
from apps.mentorship.models import MentorProfile
from utils.logging_helper import get_logger, log_exception, timed_function
from utils.api_helpers import api_response

logger = get_logger(__name__)


class CombinedBreakdownView(APIView):
    permission_classes = [IsAdminUser]

    @log_exception(logger)
    @timed_function(logger)
    def get(self, request):
        tech_journey_counts = MemberProfile.objects.values('tech_journey').annotate(
            count=Count('tech_journey')).order_by('tech_journey')

        for item in tech_journey_counts:
            item['name'] = dict(MemberProfile.CAREER_JOURNEY).get(item['tech_journey'], 'Unknown')

        response_data = {
            'skills': self.get_annotated_data(Skill, 'talent_skills_list'),
            'departments': self.get_annotated_data(Department, 'talent_department_list'),
            'roles': self.get_annotated_data(Roles, 'talent_role_types'),
            'industries': self.get_annotated_data(Industries, 'member_industries'),
            'identity_sexuality': self.get_annotated_data(SexualIdentities, 'userprofile_identity_sexuality'),
            'identity_gender': self.get_annotated_data(GenderIdentities, 'userprofile_identity_gender'),
            'identity_ethic': self.get_annotated_data(EthicIdentities, 'userprofile_identity_ethic'),
            'identity_pronouns': self.get_annotated_data(PronounsIdentities, 'userprofile_identity_pronouns'),
            'total_member': CustomUser.objects.filter(is_member=True).count(),
            'total_member_level': tech_journey_counts,
            'total_member_talent_choice': CustomUser.objects.filter(is_talent_choice=True).count(),
            'talent_choice_job_roles_needed': self.get_annotated_data(
                Roles, 'talent_role_types',
                extra_filter={'talent_role_types__user__is_talent_choice': True}
            ),
            'total_company_talent_choice': CompanyProfile.objects.filter(talent_choice_account=True).count(),
            'total_active_mentors': MentorProfile.objects.filter(mentor_status="active").count(),
            'total_mentors_applications': MentorProfile.objects.filter(mentor_status="submitted").count(),
            'total_mentors_interviewing': MentorProfile.objects.filter(mentor_status="interviewing").count(),
            'total_mentors_need_cal_info': MentorProfile.objects.filter(mentor_status="need_cal_info").count(),
        }

        return api_response(data=response_data, message="Combined breakdown data retrieved successfully")

    def get_annotated_data(self, model, related_name, extra_filter=None):
        queryset = model.objects.annotate(members_count=Count(related_name))
        if extra_filter:
            queryset = queryset.filter(**extra_filter)
        return list(queryset.filter(members_count__gt=0).order_by('-members_count').values('name', 'members_count'))
