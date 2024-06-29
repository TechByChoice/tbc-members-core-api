from django.urls import path
from apps.core.views.user_views import UserDataView, ProfileUpdateView

urlpatterns = [
    path('user-data/', UserDataView.as_view(), name='user-data'),
    path('update-profile/', ProfileUpdateView.as_view(), name='update-profile'),
]