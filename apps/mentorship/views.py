from datetime import datetime

from django.db.models import Q, Count
from rest_framework import generics, viewsets, status, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.mentorship.models import ApplicationQuestion, ApplicationAnswers, MentorshipProgramProfile, MentorProfile, \
    CommitmentLevel, MentorSupportAreas, MenteeProfile
from apps.mentorship.serializer import ApplicationQuestionSerializer, ApplicationAnswersSerializer, \
    MentorProfileSerializer
from apps.talent.models import TalentProfile
from utils.emails import send_dynamic_email
from utils.google_admin import create_user
from utils.helper import generate_random_password


class MentorListView(APIView):
    """
    View to list all mentors or create a new mentor.
    GET: Retrieve a list of all mentors.
    POST: Create a new mentor.
    """
    queryset = MentorProfile.objects.all()
    serializer_class = MentorProfileSerializer

    @permission_classes([IsAuthenticated])
    def get(self, request, format=None):
        """
        Retrieve a list of mentors or a specific mentor's details.

        This method handles GET requests sent to the MentorListView endpoint. It returns a list of all mentors
        if no specific parameters are provided. If an ID or other identifier is provided as a parameter, it returns
        the details of the specified mentor.

        Args:
            request (HttpRequest or Request): The request object containing the HTTP headers.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments. This may include parameters such as 'id' to specify a mentor.

        Returns:
            Response: A Response object containing the list of mentors or the details of a specific mentor.
                     The data is serialized into a suitable format (e.g., JSON).

        Raises:
            Http404: If a specific mentor is requested but does not exist.
            ValidationError: If the request contains invalid parameters.
        """
        mentors = MentorProfile.objects.filter(user__is_mentor_profile_active=True)
        serializer = MentorProfileSerializer(mentors, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """
        Add a new mentor to the list.

        This method handles the POST request to add a new mentor. It expects data in the
        request body containing the mentor's details, validates the data, and if valid,
        creates a new mentor record.

        Args:
            request (HttpRequest): The request object containing the POST data.
            format (str, optional): The format of the request content. Defaults to None.

        Returns:
            Response: A DRF Response object. Returns a 201 status code and the newly created mentor data
                      if successful. Returns a 400 status code and error details if the data is invalid or
                      the creation fails.

        Raises:
            ValidationError: If the provided data is not valid to create a new mentor.
            Exception: If an unexpected error occurs during mentor creation.
        """
        serializer = MentorProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MentorDetailView(APIView):
    """
    View to retrieve, update, or delete a mentor instance.
    GET: Retrieve a specific mentor.
    PUT/PATCH: Update a specific mentor.
    DELETE: Delete a specific mentor.
    """

    @permission_classes([IsAuthenticated])
    def get_object(self, pk):
        try:
            return MentorProfile.objects.get(pk=pk)
        except MentorProfile.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @permission_classes([IsAuthenticated])
    def get(self, request, pk, format=None):
        mentor = self.get_object(pk)
        serializer = MentorProfileSerializer(mentor)
        return Response(serializer.data)

    @permission_classes([IsAuthenticated])
    def put(self, request, pk, format=None):
        mentor = self.get_object(pk)
        serializer = MentorProfileSerializer(mentor, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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
            'commitment_level': data.get('commitment_level'),
            # Include other fields as necessary
        }
    )
    if created:
        user.is_mentor_application_submitted = True
        user.save()

        program_profile.mentor_profile = mentor_profile

        try:
            email_data = {
                'recipient_emails': user.email,
                'template_id': 'd-4e2837ac2bbe4127b889938e47d54f47',
            }
            send_dynamic_email(email_data)
        except Exception as e:
            print(e)
            print(f'Did not send mentor application submitted for user id: {user.id}')

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
@permission_classes([IsAuthenticated])
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
    commitment_data = data.get('commitment_level_id')
    if commitment_data is not None:
        program_profile.commitment_level.set(CommitmentLevel.objects.filter(id__in=commitment_data))
        program_profile.save()

    if user.is_mentor:
        mentor_profile, _ = MentorProfile.objects.get_or_create(user=user)
        support_area_ids = data.get('mentor_support_areas_id', [])

        if commitment_data is not None:
            mentor_profile.mentor_commitment_level.set(CommitmentLevel.objects.filter(id__in=commitment_data))
        if support_area_ids is not None:
            program_profile.mentor_support_areas.set(support_area_ids)
        mentor_profile.save()

    if user.is_mentee:
        mentee_profile, _ = MenteeProfile.objects.get_or_create(user=user)
        if mentee_profile:
            mentee_support_area_ids = data.get('mentee_support_areas_id', [])
            if mentee_support_area_ids is not None:
                mentee_profile.mentee_support_areas.set(mentee_support_area_ids)
                program_profile.mentee_support_areas.set(mentee_support_area_ids)
            mentee_profile.save()
            program_profile.save()

            if not program_profile.mentee_profile:
                program_profile.mentee_profile = mentee_profile
                program_profile.save()

    return Response({'status': True, 'message': 'Mentorship profile updated successfully'},
                    status=status.HTTP_200_OK)


# @permission_classes([IsAuthenticated])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
def update_calendar_link(request):
    user = request.user
    data = request.data

    try:
        program_profile = MentorshipProgramProfile.objects.get(user=user.id)
        mentor_profile = MentorProfile.objects.get(user=user.id)
    except MentorshipProgramProfile.DoesNotExist:
        return Response({'status': False, 'message': 'Mentorship program profile not found.'},
                        status=status.HTTP_404_NOT_FOUND)

    user.is_mentor_profile_active = True
    program_profile.calendar_link = data.get('calendar_link')
    mentor_profile.activated_at_date = datetime.utcnow()
    mentor_profile.mentor_status = 'active'
    try:
        mentor_profile.save()
        user.save()
        program_profile.save()

        return Response({'status': True, 'message': 'Calendar link updated successfully.'}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        print(f'did not send mentor approval email: {mentor_profile.id}')
        return Response({'status': False, 'message': 'We ran into an issue updating your profile.'},
                        status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_mentor_application_status(request, mentor_id):
    user = request.user
    data = request.data

    # Retrieve the MentorshipProgramProfile for the current user
    try:
        program_profile = MentorshipProgramProfile.objects.get(user=mentor_id)
        mentor_profile = MentorProfile.objects.get(user=mentor_id)
    except MentorshipProgramProfile.DoesNotExist:
        return Response({'status': 'error', 'message': 'Mentorship program profile not found.'},
                        status=status.HTTP_404_NOT_FOUND)
    try:
        current_user_mentor_profile = MentorProfile.objects.get(user__id=mentor_id)
    except Exception as e:
        current_user_mentor_profile = None
    is_user_owner_of_profile = current_user_mentor_profile.user.id == mentor_id
    if not user.is_staff and not is_user_owner_of_profile:
        return Response({'status': False, 'message': 'Values updated successfully.'},
                        status=status.HTTP_401_UNAUTHORIZED)


    # Update the values based on states

    # Need to create an email for rejected mentor
    if data.get('mentor-rejection-reason'):
        program_profile.user.is_mentor_profile_active = False
        program_profile.user.is_mentor_profile_removed = False
        mentor_profile.removed_date = datetime.utcnow()
        mentor_profile.mentor_status = request.data.get('mentor-rejection-reason')
        try:
            mentor_profile.save()
            program_profile.save()
            mentor_profile.user.save()
            return Response({'status': True,
                             'message': 'Status updated successfully.'},
                            status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'status': False,
                             'message': 'We ran into trouble updating your account. Please contact us at '
                                        'support@techbychoice.org if the issue continues.'},
                            status=status.HTTP_400_BAD_REQUEST)

    if data.get('mentor-update-status') == 'paused':
        program_profile.user.is_mentor_active = False
        mentor_profile.mentor_status = 'paused'
        mentor_profile.paused_date = datetime.utcnow()

        mentor_profile.save()
        program_profile.user.save()
        program_profile.save()

        try:
            email_data = {
                'recipient_emails': program_profile.user.email,
                'template_id': 'd-56e85c5ec90f4f149e2b8662a3d4bf64',
                'dynamic_template_data': {
                    'first_name': program_profile.user.first_name,
                }
            }
            send_dynamic_email(email_data)
            return Response({'status': True,
                             'message': 'Status updated successfully.'},
                            status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'status': False,
                             'message': 'We ran into trouble updating your account. Please contact us at '
                                        'support@techbychoice.org if the issue continues.'},
                            status=status.HTTP_400_BAD_REQUEST)

    if data.get('mentor-update-status') == 'interview-reminder':
        mentor_profile.interview_reminder_date = datetime.utcnow()

        mentor_profile.save()

        try:
            # Prepare email data
            email_data = {
                'recipient_emails': program_profile.user.email,
                'template_id': 'd-c3bf3a0d070847d9b3ef9daeac579692',
                'dynamic_template_data': {
                    'first_name': program_profile.user.first_name,
                    'interview_link': 'https://calendly.com/d/ys9-f5w-mvt/tbc-mentor-screening',
                }
            }
            email_response = send_dynamic_email(email_data)
            if email_response:
                print('email sent')
            else:
                print(f'did not send mentor approval email: {mentor_profile.id}')
        except BaseException as e:
            print(str(e))
            print('email not sent')

    if data.get('mentor-update-status') == 'approve-mentor':
        program_profile.user.is_mentor_interviewing = False
        # approved is before the cal link is live
        program_profile.user.is_mentor_profile_approved = True
        mentor_profile.mentor_status = 'need_cal_info'

        random_pas = generate_random_password()
        tbc_email = program_profile.user.first_name + '.' + program_profile.user.last_name[0] + '@techbychoice.org'
        program_profile.tbc_email = tbc_email

        mentor_profile.save()
        program_profile.save()
        program_profile.user.save()

        new_user_info = {
            'name': {'familyName': program_profile.user.last_name, 'givenName': program_profile.user.first_name},
            'password': random_pas,
            'primaryEmail': tbc_email,
            'changePasswordAtNextLogin': True
        }
        try:
            create_user(new_user_info)
            try:
                # # Prepare email data
                email_data = {
                    'recipient_emails': program_profile.user.email,
                    'template_id': 'd-73116acccef0417aacd54c6c57c6cedf',
                    'dynamic_template_data': {
                        'first_name': program_profile.user.first_name,
                        'temp_password': random_pas,
                        'tbc_email': tbc_email
                    }
                }
                send_dynamic_email(email_data)
                return Response({'status': True, 'message': 'Values updated successfully.'}, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                print(f'did not send mentor approval email: {mentor_profile.id}')
        except BaseException as e:
            print(f'Did not create gmail account mentor for mentor: {mentor_profile.id}')
            print(e)
            return Response({'status': False, 'message': 'We ran into issues creating the gmail account.'},
                            status=status.HTTP_400_BAD_REQUEST)

    if data.get('mentor-update-status') == 'active':
        program_profile.user.is_mentor_profile_active = True
        mentor_profile.mentor_status = 'active'

        mentor_profile.save()
        program_profile.save()
        program_profile.user.save()

        try:
            # # Prepare email data
            email_data = {
                'recipient_emails': program_profile.user.email,
                'template_id': 'd-e803641e82084847ad2fbcbb855d7be0',
                'dynamic_template_data': {
                    'first_name': program_profile.user.first_name,
                }
            }
            send_dynamic_email(email_data)
            return Response({'status': True, 'message': 'Values updated successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            print(f'did not send mentor approval email: {mentor_profile.id}')
            return Response({'status': False, 'message': 'We ran into issues creating the gmail account.'},
                            status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
