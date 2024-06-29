from django.urls import path
from apps.core.views.email_confirmation_views import ConfirmEmailAPIView

urlpatterns = [
    path('confirm-email/<str:id>/<str:token>/', ConfirmEmailAPIView.as_view(), name='confirm-email'),
]