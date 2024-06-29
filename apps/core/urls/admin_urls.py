from django.urls import path
from apps.core.views.admin_views import CombinedBreakdownView

urlpatterns = [
    path('admin/combined-breakdown/', CombinedBreakdownView.as_view(), name='combined-breakdown'),
]