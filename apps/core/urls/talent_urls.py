from django.urls import path
from apps.core.views.talent_views import TalentListView, TalentDetailView

urlpatterns = [
    path('talents/', TalentListView.as_view(), name='talent-list'),
    path('talents/<int:pk>/', TalentDetailView.as_view(), name='talent-detail'),
]