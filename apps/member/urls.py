from django.urls import path
from apps.member.views.member_views import MemberCreationView

urlpatterns = [
    path('create-member/', MemberCreationView.as_view(), name='create-new-member'),
]
