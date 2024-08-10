from django.urls import path
from knox import views as knox_views
from . import views
from .views_core import VerifyAdminView

urlpatterns = [
    path("login/", views.login_api),
    path("logout/", knox_views.LogoutView.as_view()),
    path("new/", views.create_new_user),
    path("new/company", views.create_new_company),
    path("details/", views.get_user_data),
    path("details/announcement", views.get_announcement),
    path("new-member/profile/create", views.create_new_member),
    path("od/profile/create", views.create_od_user_profile),
    path("details/new-company", views.get_new_company_data),
    path("profile/update/account-details", views.update_profile_account_details),
    path("profile/update/skills-roles", views.update_profile_skills_roles),
    path("profile/update/work-place", views.update_profile_work_place),
    path("profile/update/social-accounts", views.update_profile_social_accounts),
    path("profile/update/idenity", views.update_profile_identity),
    path("profile/update/notifications", views.update_profile_notifications),
    path("<int:user_id>/soft-delete/", views.soft_delete_user, name="soft-delete-user"),
    path("<int:user_id>/restore/", views.restore_user, name="restore-user"),
    path('verify-admin/', VerifyAdminView.as_view(), name='verify_admin'),
]
