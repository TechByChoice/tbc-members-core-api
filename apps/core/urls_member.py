from django.urls import path
from .views_member import MemberDetailsView

urlpatterns = [
    path("member-details/<int:pk>/", MemberDetailsView.as_view(), name="member-details")
]
