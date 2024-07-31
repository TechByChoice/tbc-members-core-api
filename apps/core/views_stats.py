from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.db.models import Count
from django.utils import timezone
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.company.models import Job, CompanyProfile, Department, Roles, Skill
from apps.core.models import CommunityNeeds
from apps.core.permissions import IsStaffUser
from apps.mentorship.models import MentorProfile
from utils.api_helpers import api_response
from utils.logging_helper import get_logger, log_exception

logger = get_logger(__name__)


class StatsAPIThrottle(UserRateThrottle):
    rate = '5/minute'


class AppStatsView(APIView):
    permission_classes = [IsStaffUser]

    # throttle_classes = [StatsAPIThrottle]

    # @log_exception(logger)
    # @timed_function(logger)
    def get(self, request):
        # Additional check for staff status
        if not request.user.is_staff:
            return api_response(message="You do not have permission to access this resource.", status=4)

        cache_key = 'app_stats_newish_test'
        cached_stats = cache.get(cache_key)

        if cached_stats:
            return api_response(data=cached_stats, message="Stats retrieved from cache")

        skills_data = self.get_top_skills()
        roles_data = self.get_top_roles()
        departments_data = self.get_top_departments()
        community_needs_data = self.get_top_community_needs()

        stats = {
            'job_board': self.get_job_board_stats(),
            'mentorship': self.get_mentorship_stats(),
            # 'company_reviews': self.get_company_review_stats(),
            'membership': self.get_user_member_data_stats(),
            'skills': skills_data,
            'skill_chart_data': self.get_pie_chart_data(skills_data, 'Skills'),
            'roles': self.get_top_roles(),
            'roles_chart_data': self.get_pie_chart_data(roles_data, 'Roles'),
            'departments': self.get_top_departments(),
            'departments_chart_data': self.get_pie_chart_data(departments_data, 'Departments'),
            'community_needs': self.get_top_community_needs(),
            'community_needs_chart_data': self.get_pie_chart_data(community_needs_data, 'CommunityNeeds'),

        }

        cache.set(cache_key, stats, 3600)  # Cache for 1 hour
        return api_response(data=stats, message="Stats retrieved successfully")

    def get_job_board_stats(self):
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE status = 'active') AS open_jobs,
                    COUNT(*) FILTER (WHERE status = 'closed') AS closed_jobs,
                    COUNT(*) FILTER (WHERE created_at >= %s) AS new_jobs
                FROM company_job
            """, [thirty_days_ago])
            job_stats = cursor.fetchone()

        return {
            'open_jobs': job_stats[0],
            'closed_jobs': job_stats[1],
            'new_jobs_last_30_days': job_stats[2],
            # 'top_jobs': self.get_top_jobs()
        }

    def get_top_jobs(self):
        return Job.objects.annotate(
            applicant_count=Count('applicants')
        ).order_by('-applicant_count')[:5].values('id', 'job_title', 'applicant_count')

    def get_mentorship_stats(self):
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE created_at >= %s) AS new_mentors,
                    COUNT(*) FILTER (WHERE mentor_status = 'active') AS active_mentors
                FROM mentorship_mentorprofile
            """, [thirty_days_ago])
            mentor_stats = cursor.fetchone()

            cursor.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE created_at >= %s) AS new_mentees,
                    COUNT(*) AS total_mentees
                FROM mentorship_menteeprofile
            """, [thirty_days_ago])
            mentee_stats = cursor.fetchone()

            cursor.execute("""
                SELECT COUNT(*) 
                FROM mentorship_session 
                WHERE created_at >= %s
            """, [thirty_days_ago])
            session_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) 
                FROM mentorship_mentorreview 
                WHERE created_at >= %s
            """, [thirty_days_ago])
            review_count = cursor.fetchone()[0]

        return {
            'new_mentors_last_30_days': mentor_stats[0],
            'active_mentors': mentor_stats[1],
            'new_mentees_last_30_days': mentee_stats[0],
            'total_mentees': mentee_stats[1],
            'sessions_last_30_days': session_count,
            'reviews_last_30_days': review_count,
            'top_mentors': self.get_top_mentors()
        }

    def get_user_member_data_stats(self):
        User = get_user_model()
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        two_weeks_ago = now - timedelta(days=14)

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE is_member = TRUE AND is_active = TRUE) AS active_members,
                    COUNT(*) FILTER (WHERE is_member = TRUE AND is_active = TRUE AND is_member_onboarding_complete = TRUE) AS completed_onboarding,
                    COUNT(*) FILTER (WHERE is_member = TRUE AND last_login < %s) AS inactive_30_days,
                    COUNT(*) FILTER (WHERE is_member = TRUE AND last_login >= %s) AS active_2_weeks,
                    COUNT(*) FILTER (WHERE is_member = TRUE AND joined_at >= %s) AS new_members_30_days
                FROM core_customuser
            """, [thirty_days_ago, two_weeks_ago, thirty_days_ago])

            result = cursor.fetchone()

        return {
            'total_active_members': result[0],
            'completed_onboarding': result[1],
            'inactive_last_30_days': result[2],
            'active_last_2_weeks': result[3],
            'new_members_last_30_days': result[4]
        }

    def get_top_mentors(self):
        return MentorProfile.objects.annotate(
            session_count=Count('mentorroster__sessions')
        ).order_by('-session_count')[:5].values('user__first_name', 'user__last_name', 'session_count')

    def get_company_review_stats(self):
        # Assuming you have a CompanyReview model

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM company_reviews_companyreview
            """)
            total_reviews = cursor.fetchone()[0]

        most_reviewed_companies = CompanyProfile.objects.annotate(
            review_count=Count('companyreview')
        ).order_by('-review_count')[:5].values('company_name', 'review_count')

        most_viewed_companies = CompanyProfile.objects.order_by('-view_count')[:5].values('company_name', 'view_count')

        return {
            'total_reviews': total_reviews,
            'most_reviewed_companies': list(most_reviewed_companies),
            'most_viewed_companies': list(most_viewed_companies)
        }

    def get_mentorship_stats(self):
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        with connection.cursor() as cursor:
            # Get detailed mentor stats
            cursor.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE created_at >= %s) AS new_mentors,
                    COUNT(*) FILTER (WHERE mentor_status = 'active') AS active_mentors,
                    COUNT(*) FILTER (WHERE mentor_status = 'submitted') AS application_mentors,
                    COUNT(*) FILTER (WHERE mentor_status = 'interviewing') AS interviewing_mentors,
                    COUNT(*) FILTER (WHERE mentor_status = 'paused') AS paused_mentors,
                    COUNT(*) FILTER (WHERE mentor_status = 'removed') AS removed_mentors
                FROM mentorship_mentorprofile
            """, [thirty_days_ago])
            mentor_stats = cursor.fetchone()

            # Get active mentee count (mentors with a roster)
            cursor.execute("""
                SELECT COUNT(DISTINCT mentee_id)
                FROM mentorship_mentorroster
                WHERE mentor_id IN (
                    SELECT id FROM mentorship_mentorprofile WHERE mentor_status = 'active'
                )
            """)
            active_mentees_count = cursor.fetchone()[0]

            # Get new mentees in the last 30 days
            cursor.execute("""
                SELECT COUNT(*)
                FROM mentorship_menteeprofile
                WHERE created_at >= %s
            """, [thirty_days_ago])
            new_mentees_count = cursor.fetchone()[0]

            # Get session and review counts
            cursor.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE created_at >= %s) AS recent_sessions,
                    COUNT(*) FILTER (WHERE is_completed = True AND completed_at >= %s) AS completed_sessions
                FROM mentorship_session
            """, [thirty_days_ago, thirty_days_ago])
            session_stats = cursor.fetchone()

            cursor.execute("""
                SELECT COUNT(*) 
                FROM mentorship_mentorreview 
                WHERE created_at >= %s
            """, [thirty_days_ago])
            review_count = cursor.fetchone()[0]

        return {
            'new_mentors_last_30_days': mentor_stats[0],
            'active_mentors': mentor_stats[1],
            'application_mentors': mentor_stats[2],
            'interviewing_mentors': mentor_stats[3],
            'paused_mentors': mentor_stats[4],
            'removed_mentors': mentor_stats[5],
            'active_mentees': active_mentees_count,
            'new_mentees_last_30_days': new_mentees_count,
            'sessions_last_30_days': session_stats[0],
            'completed_sessions_last_30_days': session_stats[1],
            'reviews_last_30_days': review_count,
            'top_mentors': self.get_top_mentors(),
        }

    @log_exception(logger)
    def get_top_skills(self):
        return self.get_top_items(Skill, 'talent_skills_list', 'skill')

    @log_exception(logger)
    def get_top_roles(self):
        return self.get_top_items(Roles, 'talent_role_types', 'role')

    @log_exception(logger)
    def get_top_departments(self):
        return self.get_top_items(Department, 'talent_department_list', 'department')

    @log_exception(logger)
    def get_top_community_needs(self):
        return self.get_top_items(CommunityNeeds, 'userprofile__tbc_program_interest', 'community need')

    def get_top_items(self, model, related_name, item_type, limit=20):
        try:
            top_items = model.objects.annotate(
                count=Count(related_name)
            ).order_by('-count')[:limit].values('name', 'count')

            return list(top_items)
        except Exception as e:
            logger.error(f"Error fetching top {item_type}s: {str(e)}")
            return []

    def get_all_items(self, model, related_name, item_type):
        try:
            items = model.objects.annotate(
                count=Count(related_name)
            ).filter(count__gt=0).order_by('-count').values('name', 'count')

            return list(items)
        except Exception as e:
            logger.error(f"Error fetching {item_type}s: {str(e)}")
            return []

    def get_pie_chart_data(self, data, field_name, top_n=20):
        """
        Generate pie chart data for any given dataset.

        :param data: List of dictionaries containing 'name' and 'count' keys
        :param field_name: Name of the field (e.g., 'skills', 'roles', 'departments')
        :param top_n: Number of top items to include individually (default 10)
        :return: List of dictionaries suitable for a pie chart
        """
        # Sort data by count in descending order
        sorted_data = sorted(data, key=lambda x: x['count'], reverse=True)

        # Get top N items
        top_items = sorted_data[:top_n]

        # Calculate the sum of all other items
        other_sum = sum(item['count'] for item in sorted_data[top_n:])

        # Prepare data for pie chart
        pie_chart_data = [
            {'name': item['name'], 'value': item['count']}
            for item in top_items
        ]

        # Add "Other" category if there are more items
        if other_sum > 0:
            pie_chart_data.append({'name': f'Other {field_name}', 'value': other_sum})

        return pie_chart_data
