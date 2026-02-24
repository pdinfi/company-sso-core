"""Tests for SSO login API view: status codes and response shape."""
import pytest
from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestSSOLoginView:
    """POST login/<provider>/ returns 200 with tokens or appropriate error."""

    def test_login_200_with_tokens(self):
        """When OAuthService.login succeeds, response 200 has access/refresh and user."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username="u2", email="u2@test.com", password="")
        with patch("company_sso_core.views.OAuthService") as MockService:
            MockService.return_value.login.return_value = (
                user,
                {"access": "tok_access", "refresh": "tok_refresh"},
            )
            api = APIClient()
            url = reverse("sso_api:login", kwargs={"provider": "google"})
            resp = api.post(
                url,
                {"code": "auth_code", "redirect_uri": "https://app.com/cb"},
                format="json",
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["access"] == "tok_access"
        assert data["refresh"] == "tok_refresh"
        assert data["user"]["email"] == "u2@test.com"

    def test_login_400_missing_code(self):
        """Missing code returns 400 validation error."""
        from rest_framework.test import APIClient
        api = APIClient()
        url = reverse("sso_api:login", kwargs={"provider": "google"})
        resp = api.post(url, {}, format="json")
        assert resp.status_code == 400

    def test_login_403_provider_disabled(self):
        """When provider is disabled, return 403."""
        from rest_framework.test import APIClient
        from company_sso_core.models import SocialProvider
        SocialProvider.objects.create(
            slug="google",
            name="Google",
            client_id="x",
            client_secret="y",
            is_active=False,
            workspace_id=None,
        )
        api = APIClient()
        url = reverse("sso_api:login", kwargs={"provider": "google"})
        resp = api.post(
            url,
            {"code": "auth_code", "redirect_uri": "https://app.com/cb"},
            format="json",
        )
        assert resp.status_code == 403
        assert "provider_disabled" in (resp.json().get("code") or "")
