from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_jobs import JobViewSet

router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="jobs")

urlpatterns = [
    path("new/", include(router.urls))
]
