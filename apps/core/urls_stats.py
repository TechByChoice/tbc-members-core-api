from django.urls import path
from .views_stats import AppStatsView

urlpatterns = [
    path('stats/', AppStatsView.as_view(), name='app_stats'),
]