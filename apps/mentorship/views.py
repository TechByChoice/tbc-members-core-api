from datetime import datetime

from django.db.models import Q, Count
from rest_framework import generics, viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.mentorship.models import ApplicationQuestion, ApplicationAnswers, MentorshipProgramProfile, MentorProfile, \
    CommitmentLevel, MentorSupportAreas, MenteeProfile
from apps.mentorship.serializer import ApplicationQuestionSerializer, ApplicationAnswersSerializer, \
    MentorProfileSerializer
from apps.talent.models import TalentProfile


class ApplicationQuestionList(generics.ListAPIView):
    queryset = ApplicationQuestion.objects.all()
    serializer_class = ApplicationQuestionSerializer


class ApplicationAnswersViewSet(viewsets.ModelViewSet):
    queryset = ApplicationAnswers.objects.all()
    serializer_class = ApplicationAnswersSerializer

    @action(detail=False, methods=['post'])
    def create_program_profile(self, request):
        # Retrieve and validate ApplicationAnswers data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create a new MentorshipProgramProfile
        program_profile = MentorshipProgramProfile.objects.create(
            user=request.user,
            # You can add other fields here based on your requirements
        )

        # Associate the ApplicationAnswers with the program profile
        answers_data = serializer.validated_data
        for answer_data in answers_data:
            ApplicationAnswers.objects.create(
                user=request.user,
                question=answer_data['question'],
                answer=answer_data['answer'],
            )

        return Response({'status': True, 'message': 'Mentorship Program Profile created successfully.'},
                        status=status.HTTP_201_CREATED)


class MentorListView(APIView):
    """
    View to list all mentors or create a new mentor.
    """
    queryset = MentorProfile.objects.all()
    serializer_class = MentorProfileSerializer

    def get(self, request, format=None):
        mentors = MentorProfile.objects.all()
        serializer = MentorProfileSerializer(mentors, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = MentorProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MentorDetailView(APIView):
    """
    View to retrieve, update, or delete a mentor instance.
    """

    def get_object(self, pk):
        try:
            return MentorProfile.objects.get(pk=pk)
        except MentorProfile.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request, pk, format=None):
        mentor = self.get_object(pk)
        serializer = MentorProfileSerializer(mentor)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        mentor = self.get_object(pk)
        serializer = MentorProfileSerializer(mentor, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        mentor = self.get_object(pk)
        mentor.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



@api_view(['GET'])
def get_mentorship_data(request):
    data = {}
    requested_fields = request.query_params.getlist('fields', [])

    if not requested_fields or 'commitment_level' in requested_fields:
        data['commitment_level'] = list(CommitmentLevel.objects.values('name', 'id'))

    if not requested_fields or 'mentor_support_areas' in requested_fields:
        data['mentor_support_areas'] = list(MentorSupportAreas.objects.values('name', 'id'))

    if not requested_fields or 'application_questions' in requested_fields:
        data['application_questions'] = list(ApplicationQuestion.objects.values('name', 'id'))

    data['status'] = True

    return Response(data)


@api_view(['POST'])
def create_or_update_mentorship_profile(request):
    user = request.user  # Get the user from the request
    data = request.data

    # Update or create MentorshipProgramProfile
    program_profile, created = MentorshipProgramProfile.objects.update_or_create(
        user=user,
        defaults={
            'biggest_strengths': data.get('biggest_strengths'),
            'career_success': data.get('career_success'),
            'career_milestones': data.get('career_milestones'),
            'career_goals': data.get('career_goals'),
            'work_motivation': data.get('work_motivation'),
            # Include other fields as necessary
        }
    )

    # Update or create MentorProfile
    mentor_profile, created = MentorProfile.objects.update_or_create(
        user=user,
        defaults={
            'mentor_support_areas': data.get('mentor_support_areas'),
            # Include other fields as necessary
        }
    )
    if created:
        user.is_mentor_application_submitted = True
        user.save()

        program_profile.mentor_profile = mentor_profile

    # Update or create MenteeProfile
    mentee_profile, created = MenteeProfile.objects.update_or_create(
        user=user,
        defaults={
            'mentee_support_areas': data.get('mentee_support_areas'),
            # Include other fields as necessary
        }
    )

    # Link the MentorshipProgramProfile to the MentorProfile and MenteeProfile
    program_profile.mentor_profile = mentor_profile
    program_profile.mentee_profile = mentee_profile
    program_profile.save()

    return Response({'status': 'success', 'message': 'Mentorship profile updated successfully'},
                    status=status.HTTP_200_OK)


@api_view(['POST'])
def update_support_type(request):
    user = request.user
    data = request.data

    # Retrieve or create MentorshipProgramProfile instance
    program_profile, create = MentorshipProgramProfile.objects.get_or_create(user=user)
    if program_profile:
        user.is_mentor_application_submitted = True
        user.is_mentor = True
        user.save()

    # Update CommitmentLevel - ManyToManyField
    commitment_data = data.get('commitment_level')
    # commitment_level_ids = commitment_data.get('commitment_level', [])
    program_profile.commitment_level.set(CommitmentLevel.objects.filter(id__in=commitment_data))
    program_profile.save()

    if user.is_mentor:
        mentor_profile, _ = MentorProfile.objects.get_or_create(user=user)
        support_area_ids = data.get('mentor_support_areas', [])
        mentor_profile.mentor_support_areas.set(support_area_ids)
        mentor_profile.save()

    if user.is_mentee:
        mentee_profile, _ = MenteeProfile.objects.get_or_create(user=user)
        if mentee_profile:
            mentee_support_area_ids = data.get('mentee_support_areas', [])
            mentee_profile.mentee_support_areas.set(mentee_support_area_ids)
            program_profile.mentee_support_areas.set(mentee_support_area_ids)
            mentee_profile.save()
            program_profile.save()
            print(mentee_profile.mentee_support_areas.all())
            if not program_profile.mentee_profile:
                program_profile.mentee_profile = mentee_profile
                program_profile.save()

    return Response({'status': True, 'message': 'Mentorship profile updated successfully'},
                    status=status.HTTP_200_OK)


# @permission_classes([IsAuthenticated])
@api_view(['POST'])
def update_career_questions(request):
    user = request.user
    data = request.data

    # Retrieve or create MentorshipProgramProfile instance
    program_profile, created = MentorshipProgramProfile.objects.get_or_create(
        user=user,
        defaults={}  # You can set default values for other fields if required
    )

    # Update fields with data from request
    program_profile.biggest_strengths = data.get('biggest_strengths', program_profile.biggest_strengths)
    program_profile.career_success = data.get('career_success', program_profile.career_success)
    program_profile.career_milestones = data.get('career_milestones', program_profile.career_milestones)
    program_profile.career_goals = data.get('career_goals', program_profile.career_goals)
    program_profile.work_motivation = data.get('work_motivation', program_profile.work_motivation)

    # Save the updated profile
    program_profile.save()

    return Response({'status': 'success', 'message': 'Career questions updated successfully'},
                    status=status.HTTP_200_OK)

# @permission_classes([IsAuthenticated])
@api_view(['POST'])
def update_profile_questions(request):
    user = request.user
    data = request.data

    # Retrieve or create MentorshipProgramProfile instance
    program_profile, created = MentorProfile.objects.get_or_create(
        user=user,
        defaults={}  # You can set default values for other fields if required
    )

    # Update fields with data from request
    program_profile.mentorship_goals = data.get('mentorship_goals', program_profile.mentorship_goals)
    program_profile.mentor_how_to_help = data.get('mentor_how_to_help', program_profile.mentor_how_to_help)

    # Save the updated profile
    program_profile.save()

    return Response({'status': 'success', 'message': 'Mentor Profile questions updated successfully'},
                    status=status.HTTP_200_OK)


@api_view(['POST'])
def update_values_questions(request):
    user = request.user
    data = request.data

    # Retrieve the MentorshipProgramProfile for the current user
    try:
        program_profile = MentorshipProgramProfile.objects.get(user=user)
    except MentorshipProgramProfile.DoesNotExist:
        return Response({'status': 'error', 'message': 'Mentorship program profile not found.'},
                        status=status.HTTP_404_NOT_FOUND)

    # Update the values
    program_profile.value_power = data.get('power')
    program_profile.value_achievement = data.get('achievement')
    program_profile.value_hedonism = data.get('hedonism')
    program_profile.value_stimulation = data.get('stimulation')
    program_profile.value_self_direction = data.get('self_direction')
    program_profile.value_universalism = data.get('universalism')
    program_profile.value_benevolence = data.get('benevolence')
    program_profile.value_tradition = data.get('tradition')
    program_profile.value_conformity = data.get('conformity')
    program_profile.value_security = data.get('security')

    # Save the updates
    program_profile.save()

    return Response({'status': True, 'message': 'Values updated successfully.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def update_mentor_application_status(request, mentor_id):
    user = request.user
    data = request.data
    if not user.is_staff:
        return Response({'status': False, 'message': 'Values updated successfully.'}, status=status.HTTP_401_UNAUTHORIZED)
    # Retrieve the MentorshipProgramProfile for the current user
    try:
        program_profile = MentorshipProgramProfile.objects.get(user=mentor_id)
        mentor_profile = MentorProfile.objects.get(user=mentor_id)
    except MentorshipProgramProfile.DoesNotExist:
        return Response({'status': 'error', 'message': 'Mentorship program profile not found.'},
                        status=status.HTTP_404_NOT_FOUND)

    # Update the values based on states
    if data.get('mentor-rejection-reason'):
        program_profile.user.is_mentor_profile_active = False
        program_profile.user.is_mentor_profile_removed = False
        mentor_profile.removed_date = datetime.utcnow()
        mentor_profile.mentor_status = request.data.get('mentor-rejection-reason')
        mentor_profile.save()
        program_profile.save()

    return Response({'status': True, 'message': 'Values updated successfully.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_top_mentor_match(request):
    """
    Retrieve top mentor profile.
    """
    talent_profile = TalentProfile.objects.get(user=request.user.id)

    # Extract skills, roles, and departments
    talent_skills = talent_profile.skills.all()
    talent_roles = talent_profile.role.all()
    talent_departments = talent_profile.department.all()

    # Filter only mentor profiles (adjust this according to your model)
    mentor_profiles = TalentProfile.objects.filter(user__is_mentor=True)

    # Create separate Q objects for each criteria
    skills_query = Q(skills__in=talent_skills)
    roles_query = Q(role__in=talent_roles)
    departments_query = Q(department__in=talent_departments)

    # Combine queries using OR logic
    combined_query = skills_query | roles_query | departments_query

    # Filter and annotate mentor instances
    matching_mentor = mentor_profiles.filter(combined_query).distinct().annotate(
        score=Count('skills', filter=Q(skills__in=talent_skills.values_list('id', flat=True))) +
              Count('role', filter=Q(role__in=talent_roles.values_list('id', flat=True))) +
              Count('department', filter=Q(department__in=talent_departments.values_list('id', flat=True)))
    ).order_by('-score')

    # Serialize the results
    matching_mentors_serialized = MentorProfileSerializer(matching_mentor, many=True).data

    # Return the response
    return Response({'status': True, 'matching_mentors': matching_mentors_serialized}, status=status.HTTP_200_OK)
