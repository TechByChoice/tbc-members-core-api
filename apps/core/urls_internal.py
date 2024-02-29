from django.urls import path

from apps.core.views_internal import ExternalView

urlpatterns = [path("user-demo/", ExternalView.as_view(), name="user-demo")]
