from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_company import CompanyView

# Initialize the router and register your viewsets
router = DefaultRouter()
router.register(r"info", CompanyView, basename="company")

# Your project's URL patterns
urlpatterns = [
    path("", include(router.urls))
]
