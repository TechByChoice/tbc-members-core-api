from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from utils.logging_helper import get_logger, log_exception, timed_function
from .models import MentorProfile, MenteeProfile, MentorshipProgramProfile, Session
from django.shortcuts import get_object_or_404

from .serializers.mentorship import MentorRosterSerializer, SessionSerializer
from .serializer import MentorReviewSerializer

logger = get_logger(__name__)


class MentorshipRelationshipView(APIView):
    @log_exception(logger)
    @timed_function(logger)
    def post(self, request, mentor_id=None):
        """
        Create a new mentor-mentee connection and associated session.

        Args:
            request (Request): The HTTP request object.
            mentor_id (int): The ID of the mentor to connect with.

        Returns:
            Response: HTTP response with the created data or error messages.
        """
        try:
            with transaction.atomic():
                mentor = self._get_mentor(mentor_id)
                print("Got mentor")
                mentee_profile = self._get_or_create_mentee_profile(request.user)
                print("Got mentee profile")
                mentor_roster = self._create_mentor_roster(mentor, mentee_profile)
                print("Got mentee roster")
                session = self._create_session(
                    user_id=request.user.id,
                    mentor_support_areas=request.data.get('mentor_support_areas', []),
                    mentor_booking_note=request.data.get('mentor_booking_note', ''),
                    mentor_roster=mentor_roster
                )
                print("Got session")

                return Response(
                    {
                        "status": True,
                        "mentor_roster": MentorRosterSerializer(mentor_roster).data,
                        "session": SessionSerializer(session).data,
                    },
                    status=status.HTTP_201_CREATED,
                )

        except Exception as e:
            logger.error(f"Error creating mentor-mentee connection: {str(e)}")
            return Response(
                {"detail": "An error occurred while processing your request."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    #  Helper

    def _get_mentor(self, mentor_id):
        """Get the mentor object or raise a 404 error."""
        return get_object_or_404(MentorProfile, user_id=mentor_id)

    def _get_or_create_mentee_profile(self, user):
        """Get or create a mentee profile for the user."""
        mentee_profile, created = MenteeProfile.objects.get_or_create(user=user)
        if created:
            user.is_mentee = True
            user.save(update_fields=['is_mentee'])
        return mentee_profile

    def _create_mentor_roster(self, mentor, mentee_profile):
        """Create a new MentorRoster object."""
        roster_data = {
            "mentor": mentor.id,
            "mentee": mentee_profile.id
        }
        print(f"Attempting to create MentorRoster with data: {roster_data}")

        serializer = MentorRosterSerializer(data=roster_data)

        if serializer.is_valid():
            print(f"Serializer is valid. Validated data: {serializer.validated_data}")
            if not serializer.validated_data:
                print("Serializer is valid but validated_data is empty")
                raise ValidationError("Serializer validated_data is empty")
            try:
                mentor_roster = serializer.save()
                print(f"MentorRoster created successfully with id: {mentor_roster.id}")
                return mentor_roster
            except Exception as e:
                print(f"Error saving MentorRoster: {str(e)}")
                raise
        else:
            print(f"Serializer errors: {serializer.errors}")
            raise ValidationError(serializer.errors)

    def _create_session(self, user_id, mentor_support_areas, mentor_booking_note, mentor_roster):
        """Create a new Session object."""
        session_data = {
            "mentor_mentee_connection": mentor_roster.id,
            "created_by": user_id,
            "note": mentor_booking_note,
        }
        serializer = SessionSerializer(data=session_data)
        serializer.is_valid(raise_exception=True)
        session = serializer.save()
        session.reason.set(mentor_support_areas)
        return session


class MentorshipReviewsView(APIView):
    def post(self, request, mentor_id):
        mentor = get_object_or_404(MentorProfile, id=mentor_id)
        user = request.user
        mentee = get_object_or_404(MenteeProfile, user_id=user.id)
        review_data = {
            "mentor": mentor.id,
            "mentee": mentee.id,
            "rating": request.data.get("rating"),
            "review_content": request.data.get("mentorship_goals"),
            "review_author": "mentee",
        }
        serializer = MentorReviewSerializer(data=review_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
