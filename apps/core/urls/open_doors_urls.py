from django.urls import path
from apps.core.views.open_doors_views import UserManagementView

urlpatterns = [
    path('open-doors/register/', UserManagementView.as_view({'post': 'create'}), name='open-doors-register'),
    path('open-doors/confirm-agreement/', UserManagementView.as_view({'post': 'service_agreement'}),
         name='open-doors-confirm-agreement'),
    path('open-doors/update-profile/', UserManagementView.as_view({'patch': 'partial_update'}),
         name='open-doors-update-profile'),
    path('open-doors/submit-report/', UserManagementView.as_view({'post': 'post_review_submission'}),
         name='open-doors-submit-report'),
    path('open-doors/get-report/<int:pk>/', UserManagementView.as_view({'get': 'get_review_submission'}),
         name='open-doors-get-report'),
]
