from django.urls import path

from .views_auth import UserPermissionAPIView, PasswordResetRequestView, PasswordResetConfirmView

urlpatterns = [
    path("", UserPermissionAPIView.as_view(), name="auth"),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
