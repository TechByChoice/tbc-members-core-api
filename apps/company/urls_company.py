from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_company import CompanyView

# Initialize the router and register your viewsets

# Your project's URL patterns
urlpatterns = [
    path("companies/<int:pk>/", CompanyView.as_view(), name='company-detail'),
]