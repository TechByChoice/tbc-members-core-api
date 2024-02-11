from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import MentorProfile, MenteeProfile, MentorshipProgramProfile, Session
from django.shortcuts import get_object_or_404

from .serializer import MentorRosterSerializer, MentorReviewSerializer


class MentorshipRelationshipView(APIView):
    def post(self, request, mentor_id=None):
        mentor = get_object_or_404(MentorProfile, user_id=mentor_id)
        user = request.user

        # Get or create a mentee profile for the user
        mentee_program_app, created = MenteeProfile.objects.get_or_create(user=user)
        if created:
            mentee_profile = MenteeProfile.objects.create(user=user)

            mentee_program_app.mentee_profile = mentee_profile
            mentee_program_app.save()

            user.is_mentee = True
            user.save()

        roster_data = {"mentor": mentor.id, "mentee": mentee_program_app.id}

        serializer = MentorRosterSerializer(data=roster_data)
        if serializer.is_valid():
            mentor_roster = serializer.save()

            # Create a new Session object and associate it with the MentorRoster
            new_session = Session.objects.create(
                mentor_mentee_connection=mentor_roster, created_by=user
            )
            # Add the new session to the mentor_roster

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
