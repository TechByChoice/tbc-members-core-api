from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views
from .views import MentorListView, MentorDetailView, get_mentorship_data, update_support_type, update_career_questions, \
    update_values_questions, update_profile_questions, get_top_mentor_match

router = DefaultRouter()
router.register(r'mentors', views.MentorListView)

urlpatterns = [
    path('questions/', views.ApplicationQuestionList.as_view(), name='question-list'),
    path('details/', get_mentorship_data, name='details'),
    path('update/support/', update_support_type, name='update-support'),
    path('update/career/', update_career_questions, name='update-career-questions'),
    path('update/value/', update_values_questions, name='update-value-questions'),
    path('update/profile/', update_profile_questions, name='update_profile_questions'),
    path('mentor-match/', get_top_mentor_match, name='mentor-match'),
    path('', MentorListView.as_view(), name='mentor-list'),
    path('<int:pk>/', MentorDetailView.as_view(), name='mentor-detail'),
]