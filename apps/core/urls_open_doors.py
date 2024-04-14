from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.core.views_open_doors import UserManagementView

router = DefaultRouter()
router.register(r'onboarding', UserManagementView, basename='onboarding')

urlpatterns = [
    path('', include(router.urls)),
]
