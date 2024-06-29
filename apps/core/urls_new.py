from django.urls import path, include

urlpatterns = [
    path('', include('apps.core.urls.auth_urls')),
    path('', include('apps.core.urls.user_urls')),
    path('', include('apps.core.urls.talent_urls')),
    path('', include('apps.core.urls.company_urls')),
    path('', include('apps.core.urls.admin_urls')),
    path('', include('apps.core.urls.dropdown_urls')),
    path('', include('apps.core.urls.open_doors_urls')),
    path('', include('apps.core.urls.email_confirmation_urls')),
]