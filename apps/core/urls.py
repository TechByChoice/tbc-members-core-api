from django.urls import path
from knox import views as knox_views
from . import views


urlpatterns = [
    path('login/', views.login_api),
    path('logout/', knox_views.LogoutView.as_view()),
    path('new/', views.create_new_user),
    path('details/', views.get_user_data),
    path('details/new-member', views.get_new_member_data),
    path('details/announcement', views.get_announcement),
    path('new-member/profile/create', views.create_new_member),
    path('details/new-company', views.get_new_company_data),
    path('profile/update/account-details', views.update_profile_account_details),
    path('profile/update/skills-roles', views.update_profile_skills_roles),
    path('profile/update/work-place', views.update_profile_work_place),
    path('profile/update/social-accounts', views.update_profile_social_accounts),
    path('profile/update/idenity', views.update_profile_identity),
    path('profile/update/notifications', views.update_profile_notifications),
]
