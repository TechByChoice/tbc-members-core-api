from django.urls import path

from . import views_core

urlpatterns = [
    path("details/", views_core.get_dropdown_data, name="details"),
    path("member/all/", views_core.get_all_members, name="members")
]
