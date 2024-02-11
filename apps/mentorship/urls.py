from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views
from .views import MentorListView, MentorDetailView
from .views_relationship_managment import (
    MentorshipRelationshipView,
    MentorshipReviewsView,
)

router = DefaultRouter()
router.register(r"mentors", views.MentorListView)

urlpatterns = [
    path("details/", views.get_mentorship_data, name="details"),
    path("update/support/", views.update_support_type, name="update-support"),
    path(
        "update/career/", views.update_career_questions, name="update-career-questions"
    ),
    path("update/value/", views.update_values_questions, name="update-value-questions"),
    path(
        "update/profile/",
        views.update_profile_questions,
        name="update_profile_questions",
    ),
    path(
        "update/calendar-link/", views.update_calendar_link, name="update_calendar_link"
    ),
    path("mentor-match/", views.get_top_mentor_match, name="mentor-match"),
    path("", MentorListView.as_view(), name="mentor-list"),
    path("connect", MentorshipRelationshipView.as_view(), name="mentor-connect"),
    path(
        "mentor/<int:mentor_id>/connect/roster/add",
        MentorshipRelationshipView.as_view(),
        name="mentor-connect",
    ),
    path(
        "mentor/<int:mentor_id>/update-status/",
        views.update_mentor_application_status,
        name="update_mentor_application_status",
    ),
    path("<int:pk>/", MentorDetailView.as_view(), name="mentor-detail"),
    path(
        "reviews/<int:mentor_id>/",
        MentorshipReviewsView.as_view(),
        name="review-mentor",
    ),
]
