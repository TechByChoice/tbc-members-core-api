from django.urls import path
from apps.core.views.company_views import CompanyViewSet

urlpatterns = [
    path('company/create-onboarding/', CompanyViewSet.as_view({'post': 'create_onboarding'}),
         name='company-create-onboarding'),
]
