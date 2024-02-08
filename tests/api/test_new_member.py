from django.test import TestCase, RequestFactory
from unittest.mock import patch, MagicMock
from rest_framework import status
from django.contrib.auth.models import User

from apps.core.models import UserProfile
from apps.core.util import update_talent_profile, update_user, update_user_profile, \
    extract_user_data, extract_company_data, process_company_types
from apps.core.views import create_new_member
from apps.talent.models import TalentProfile


class CreateNewMemberTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create(username='testuser', email='test@example.com')
        self.request = self.factory.patch('/api/member', {'data': 'test_data'}, format='json')
        self.request.user = self.user

    @patch('apps.core.util.extract_user_data')
    @patch('apps.core.util.extract_company_data')
    @patch('apps.core.util.extract_profile_data')
    @patch('apps.core.util.extract_talent_data')
    @patch('apps.core.util.update_user')
    @patch('apps.core.util.update_talent_profile')
    @patch('apps.core.util.update_user_profile')
    @patch('utils.slack.send_invite')
    def test_create_new_member_success(self, mock_send_invite, mock_create_or_update_user_profile,
                                       mock_create_or_update_talent_profile, mock_create_or_update_user,
                                       mock_extract_talent_data, mock_extract_profile_data, mock_extract_company_data,
                                       mock_extract_user_data):
        # Mocking the extract functions to return expected data
        mock_extract_user_data.return_value = {'is_mentee': True, 'is_mentor': False}
        mock_extract_company_data.return_value = {'company_name': 'TestCompany',
                                                  'company_url': 'https://testcompany.com'}
        mock_extract_profile_data.return_value = {'linkedin': 'https://linkedin.com/in/test'}
        mock_extract_talent_data.return_value = {'tech_journey': '5 years', 'is_talent_status': True}

        # Mocking the create_or_update functions to return model instances
        mock_create_or_update_user.return_value = self.user
        mock_create_or_update_talent_profile.return_value = TalentProfile.objects.create(user=self.user)
        mock_create_or_update_user_profile.return_value = UserProfile.objects.create(user=self.user)

        # Call the create_new_member function
        response = create_new_member(self.request)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data,
                         {'status': True, 'message': 'User, TalentProfile, and UserProfile created successfully!'})
        mock_send_invite.assert_called_once_with(self.user.email)


class CreateUserTestCase(TestCase):
    def setUp(self):
        self.user_data = {'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
        self.user = User.objects.create(username='testuser', email=self.user_data['email'])

    @patch('path.to.serializers.UpdateCustomUserSerializer')
    def test_create_or_update_user_success(self, mock_user_serializer):
        # Mocking the serializer's return value and is_valid method
        mock_user_serializer.return_value.is_valid.return_value = True
        mock_user_serializer.return_value.save.return_value = self.user

        result = update_user(self.user, self.user_data)

        # Assertions
        mock_user_serializer.assert_called_once_with(instance=self.user, data=self.user_data, partial=True)
        mock_user_serializer.return_value.is_valid.assert_called_once()
        self.assertEqual(result, self.user)


class CreateTalentProfileTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', email='test@example.com')
        self.talent_data = {'tech_journey': '5 years', 'is_talent_status': True}

    @patch('path.to.models.TalentProfile.objects.get_or_create')
    def test_create_or_update_talent_profile_success(self, mock_get_or_create):
        mock_talent_profile = MagicMock()
        mock_get_or_create.return_value = (mock_talent_profile, True)

        result = update_talent_profile(self.user, self.talent_data)

        # Assertions
        mock_get_or_create.assert_called_once_with(user=self.user)
        self.assertEqual(result, mock_talent_profile)

    # Add more test cases for different scenarios, handling exceptions, etc.


class CreateUserProfileTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', email='test@example.com')
        self.profile_data = {'linkedin': 'https://linkedin.com/in/test'}

    @patch('path.to.models.UserProfile.objects.get_or_create')
    def test_create_or_update_user_profile_success(self, mock_get_or_create):
        mock_user_profile = MagicMock()
        mock_get_or_create.return_value = (mock_user_profile, True)

        result = update_user_profile(self.user, self.profile_data)

        # Assertions
        mock_get_or_create.assert_called_once_with(user=self.user, defaults=self.profile_data)
        self.assertEqual(result, mock_user_profile)

    # Add more test cases for different scenarios, handling exceptions, etc.


class ExtractUserDataTestCase(TestCase):
    def test_extract_user_data(self):
        input_data = {'is_mentee': True, 'is_mentor': False}
        expected_result = {'is_mentee': True, 'is_mentor': False}

        result = extract_user_data(input_data)

        self.assertEqual(result, expected_result)

    # Add more test cases for different scenarios, input variations, etc.


class ExtractCompanyDataTestCase(TestCase):
    def test_extract_company_data(self):
        input_data = {'company_name': 'TestCompany', 'company_url': 'https://testcompany.com'}
        expected_result = {'company_name': 'TestCompany', 'company_url': 'https://testcompany.com'}

        result = extract_company_data(input_data)

        self.assertEqual(result, expected_result)

    # Add more test cases for different scenarios, input variations, etc.


class ProcessCompanyTypesTestCase(TestCase):
    @patch('path.to.models.CompanyTypes.objects.get_or_create')
    def test_process_company_types_success(self, mock_get_or_create):
        input_types = ['Tech', 'Finance']
        mock_company_type = MagicMock()
        mock_get_or_create.side_effect = [(mock_company_type, True), (mock_company_type, True)]

        result = process_company_types(input_types)

        self.assertEqual(len(result), 2)
        self.assertTrue(all(type_ == mock_company_type for type_ in result))
        mock_get_or_create.assert_has_calls([call(name='Tech'), call(name='Finance')])

    # Add more test cases for different scenarios, especially error handling.
