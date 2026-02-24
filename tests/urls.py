"""Test URL config: mount SSO URLs under api/v1/sso/."""
from django.urls import path, include

urlpatterns = [
    path("api/v1/sso/", include("company_sso_core.urls")),
]
