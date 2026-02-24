"""URL configuration for SSO API. Host project includes under e.g. api/v1/sso/."""
from django.urls import path

from company_sso_core.views import SSOLoginView

app_name = "sso_api"

urlpatterns = [
    path("login/<str:provider>/", SSOLoginView.as_view(), name="login"),
]
