from django.urls import path

from . import views_core
from .views_admin import CombinedBreakdownView

urlpatterns = [
    path("details/", views_core.get_dropdown_data, name="details"),
    path("member/all/", views_core.get_all_members, name="members"),
    path('all-breakdowns/', CombinedBreakdownView.as_view(), name='all-breakdowns'),
]
