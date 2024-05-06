"""api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("user/", include("apps.core.urls")),
    path("app/", include("apps.core.urls_core")),
    path("member/", include("apps.core.urls_member")),
    path("mentorship/", include("apps.mentorship.urls")),
    path("company/", include("apps.company.urls")),
    path("open-doors/", include("apps.core.urls_open_doors")),
    path("talent-choice/company/", include("apps.core.urls_talent_choice")),
    path("company-profile/", include("apps.company.urls_company")),
    path("event/", include("apps.event.urls")),
    path("api/", include("apps.core.urls_internal")),
    path("auth/", include("apps.core.urls_auth")),
]
