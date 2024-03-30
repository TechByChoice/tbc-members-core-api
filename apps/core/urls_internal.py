from django.urls import path

from apps.core.views_internal import ExternalView

from . import views_internal

urlpatterns = [
    path("user-demo/", ExternalView.as_view(), name="user-demo"),
    path("update/review-token/", views_internal.ExternalView.update_review_token_total)
]
