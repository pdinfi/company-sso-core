"""Tests for provider registry: auto-registration and get_provider."""
import pytest

from company_sso_core.providers import (
    get_provider,
    get_provider_registry,
    get_all_provider_slugs,
)
from company_sso_core.providers.base import BaseOAuthProvider
from company_sso_core.exceptions import ProviderNotConfiguredError


class TestProviderRegistry:
    """Registry is populated by metaclass; get_provider returns instance."""

    def test_google_registered(self):
        """Google provider is in registry after importing providers."""
        registry = get_provider_registry()
        assert "google" in registry
        assert registry["google"].slug == "google"

    def test_github_facebook_registered(self):
        """GitHub and Facebook are registered."""
        registry = get_provider_registry()
        assert "github" in registry
        assert "facebook" in registry

    def test_get_provider_returns_instance(self):
        """get_provider(slug, credentials) returns provider instance."""
        provider = get_provider("google", {"client_id": "x", "client_secret": "y"})
        assert provider is not None
        assert provider.slug == "google"
        assert provider.credentials["client_id"] == "x"

    def test_get_provider_unknown_raises(self):
        """Unknown slug raises ProviderNotConfiguredError."""
        with pytest.raises(ProviderNotConfiguredError):
            get_provider("unknown_slug", {})

    def test_get_provider_generic_builtin(self):
        """get_provider(slug, credentials) returns GenericOAuth2Provider for built-in configs."""
        provider = get_provider("microsoft", {"client_id": "x", "client_secret": "y"})
        assert provider is not None
        assert provider.slug == "microsoft"
        assert provider.credentials["client_id"] == "x"
        assert provider.token_url

    def test_get_all_provider_slugs_50_plus(self):
        """At least 50 SSO provider slugs are supported."""
        slugs = get_all_provider_slugs()
        assert len(slugs) >= 50
        assert "google" in slugs
        assert "github" in slugs
        assert "facebook" in slugs
        assert "microsoft" in slugs
        assert "linkedin" in slugs
