from django.urls import path

from .views_auth import UserPermissionAPIView

urlpatterns = [
    path("", UserPermissionAPIView.as_view(), name="auth")
]
