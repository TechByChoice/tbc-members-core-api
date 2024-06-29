from django.urls import path

from apps.core.views.auth_views import UserPermissionAPIView, LoginView, PasswordResetRequestView, \
    PasswordResetConfirmView

urlpatterns = [
    path('permissions/', UserPermissionAPIView.as_view(), name='user-permissions'),
    path('login/', LoginView.as_view(), name='login'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(),
         name='password-reset-confirm'),
]
