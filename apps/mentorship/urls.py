from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views
from . import views_relationship_managment
from .views import MentorListView, MentorDetailView
from .views_relationship_managment import MentorshipRelationshipView

router = DefaultRouter()
router.register(r'mentors', views.MentorListView)
# router.register(r'connect', views_relationship_managment.MentorshipRelationshipView, basename='relation')

urlpatterns = [
    path('questions/', views.ApplicationQuestionList.as_view(), name='question-list'),
    path('details/', views.get_mentorship_data, name='details'),
    path('update/support/', views.update_support_type, name='update-support'),
    path('update/career/', views.update_career_questions, name='update-career-questions'),
    path('update/value/', views.update_values_questions, name='update-value-questions'),
    path('update/profile/', views.update_profile_questions, name='update_profile_questions'),
    path('mentor-match/', views.get_top_mentor_match, name='mentor-match'),
    path('', MentorListView.as_view(), name='mentor-list'),
    path('connect', MentorshipRelationshipView.as_view(), name='mentor-connect'),
    path('mentor/<int:mentor_id>/connect/roster/add', MentorshipRelationshipView.as_view(), name='mentor-connect'),
    path('<int:pk>/', MentorDetailView.as_view(), name='mentor-detail'),
]
