from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from apps.company.models import Skill, Roles
from apps.core import views
from apps.core.models import SexualIdentities, GenderIdentities, EthicIdentities


class NewMemberDataTests(TestCase):
    # fixtures = ['path_to_your_fixture_file.json']  # if you are using fixtures

    def setUp(self):
        # If you're not using fixtures, you can create and save test data here.
        # e.g., SexualIdentities.objects.create(name="Identity1")
        # Creating test data for SexualIdentities
        SexualIdentities.objects.create(identity="TestIdentity1")
        SexualIdentities.objects.create(identity="TestIdentity2")

        # Creating test data for GenderIdentities
        GenderIdentities.objects.create(gender="TestGender1")
        GenderIdentities.objects.create(gender="TestGender2")

        # Creating test data for EthicIdentities
        EthicIdentities.objects.create(ethnicity="TestEthnicity1")
        EthicIdentities.objects.create(ethnicity="TestEthnicity2")

        # ... Add similar blocks for other models like PronounsIdentities, Skill, Department, etc.

        # For models with foreign keys or many-to-many relationships, ensure you create the related objects first.
        # For example, if Roles has a ManyToMany relationship with Skill:
        skill1 = Skill.objects.create(name="TestSkill1", skill_type="Type1")
        skill2 = Skill.objects.create(name="TestSkill2", skill_type="Type2")
        role = Roles.objects.create(name="TestRole1")
        role.job_skill_list.set([skill1, skill2])

    def test_get_new_member_data(self):
        response = self.client.get(
            reverse(views.get_new_member_data))  # Replace with the name of your view if you're using named URLs.
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the returned data structure matches the expected one.
        # Here's a small example for just one part:
        self.assertIn('total_companies', response.data)
        self.assertIn('data', response.data)
        self.assertEqual(len(response.data['data']), 5)  # You have 3 main steps in your data.

        # Optionally, check if the data in the response matches your test data.
        # e.g.,
        # self.assertIn({'name': 'Identity1'}, response.data['data'][0]['questions'][1]['options'])

        # You can add more assertions as necessary for other parts of the response.
