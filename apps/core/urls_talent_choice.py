from django.urls import path, re_path
from .views_member import MemberDetailsView
from .views_talent_choice import CompanyViewSet, ConfirmEmailAPIView

urlpatterns = [
    path("member-details/<int:pk>/", MemberDetailsView.as_view(), name="member-details"),
    path("confirm-agreement/", CompanyViewSet.as_view({
        'post': 'service_agreement'
    }), name="service-agreement"),
    path("complete-onboarding/", CompanyViewSet.as_view({
        'post': 'complete_onboarding'
    }), name="complete-onboarding"),
    path("onboarding/create/profile/", CompanyViewSet.as_view({
        'post': 'create_onboarding'
    }), name="create-onboarding"),
    re_path(r'^confirm-email/(?P<id>[^/.]+)/(?P<token>[^/.]+)/$',
            ConfirmEmailAPIView.as_view(),
            name="confirm-account-email"),
]
