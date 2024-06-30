from django.urls import path
from apps.core.views.user_views import UserDataView, ProfileUpdateView, get_announcement, UserProfileManagementView, \
    CompanyRegistrationView, UserRegistrationView, MemberCreationView

urlpatterns = [
    path('user-data/', UserDataView.as_view(), name='user-data'),
    path('update-profile/', ProfileUpdateView.as_view(), name='update-profile'),
    path('register/', UserRegistrationView.as_view(), name='register-user'),
    path('register-company/', CompanyRegistrationView.as_view(), name='register-company'),
    path('update-notifications/', UserProfileManagementView.as_view({'post': 'update_notifications'}),
         name='update-notifications'),
    path('update-identity/', UserProfileManagementView.as_view({'post': 'update_identity'}), name='update-identity'),
    path('update-social-accounts/', UserProfileManagementView.as_view({'post': 'update_social_accounts'}),
         name='update-social-accounts'),
    path('update-skills-roles/', UserProfileManagementView.as_view({'post': 'update_skills_roles'}),
         name='update-skills-roles'),
    path('update-work-place/', UserProfileManagementView.as_view({'post': 'update_work_place'}),
         name='update-work-place'),
    path('update-account-details/', UserProfileManagementView.as_view({'post': 'update_account_details'}),
         name='update-account-details'),
    path('announcement/', get_announcement, name='announcement'),
    path('create-new-member/', MemberCreationView.as_view(), name='create-new-member')
]
