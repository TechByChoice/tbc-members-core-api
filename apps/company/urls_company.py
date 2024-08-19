from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_company import CompanyView

# Initialize the router and register your viewsets
router = DefaultRouter()
router.register(r"info", CompanyView, basename="company")

# Your project's URL patterns
urlpatterns = [
    path("", include(router.urls)),
    path("<int:pk>/soft-delete/", CompanyView.as_view({'post': 'soft_delete_company'}), name="soft-delete-company"),
    path("<int:pk>/restore/", CompanyView.as_view({'post': 'restore_company'}), name="restore-company"),
    path("<int:pk>/simple/", CompanyView.as_view({'get': 'get_name'}), name="get_name"),
]
