"""Tests for credential_loader: DB primary, then settings fallback."""
import pytest
from django.conf import settings
from unittest.mock import patch

from company_sso_core.models import SocialProvider
from company_sso_core.services.credential_loader import get_provider_credentials
from company_sso_core.exceptions import ProviderNotConfiguredError


@pytest.mark.django_db
class TestCredentialLoader:
    """Credential resolution: DB then settings then raise."""

    def test_from_settings_when_no_db(self):
        """When no SocialProvider in DB, use settings.SSO_PROVIDERS."""
        creds = get_provider_credentials("google", workspace=None)
        assert creds["client_id"] == "test_google_client_id"
        assert creds["client_secret"] == "test_google_client_secret"
        assert "extra_config" in creds

    def test_from_db_when_exists(self):
        """When SocialProvider exists in DB, use DB credentials (primary)."""
        SocialProvider.objects.create(
            slug="google",
            name="Google",
            client_id="db_client_id",
            client_secret="db_client_secret",
            is_active=True,
            workspace_id=None,
        )
        creds = get_provider_credentials("google", workspace=None)
        assert creds["client_id"] == "db_client_id"
        assert creds["client_secret"] == "db_client_secret"

    def test_workspace_specific(self):
        """When workspace_id provided, use workspace-scoped provider."""
        SocialProvider.objects.create(
            slug="google",
            name="Google",
            client_id="global_id",
            client_secret="global_secret",
            is_active=True,
            workspace_id=None,
        )
        SocialProvider.objects.create(
            slug="google",
            name="Google Workspace",
            client_id="ws_id",
            client_secret="ws_secret",
            is_active=True,
            workspace_id=1,
        )
        creds = get_provider_credentials("google", workspace=1)
        assert creds["client_id"] == "ws_id"
        assert creds["client_secret"] == "ws_secret"
        creds_global = get_provider_credentials("google", workspace=None)
        assert creds_global["client_id"] == "global_id"

    def test_inactive_provider_not_returned(self):
        """Inactive provider in DB is skipped; fallback to settings."""
        SocialProvider.objects.create(
            slug="google",
            name="Google",
            client_id="db_inactive_id",
            client_secret="db_inactive_secret",
            is_active=False,
            workspace_id=None,
        )
        creds = get_provider_credentials("google", workspace=None)
        assert creds["client_id"] == "test_google_client_id"

    def test_raises_when_not_configured(self):
        """Unknown provider raises ProviderNotConfiguredError."""
        with pytest.raises(ProviderNotConfiguredError):
            get_provider_credentials("unknown_provider", workspace=None)

    def test_raises_when_settings_empty(self):
        """No DB and no settings for slug raises."""
        with patch.object(settings, "SSO_PROVIDERS", {}):
            with pytest.raises(ProviderNotConfiguredError):
                get_provider_credentials("google", workspace=None)
