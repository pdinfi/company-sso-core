"""Tests for OAuthService.login: credentials, exchange, user resolution, tokens, log."""
import pytest
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model

from company_sso_core.models import SSOLoginLog
from company_sso_core.services.oauth_service import OAuthService
from company_sso_core.exceptions import (
    ProviderDisabledError,
    ProviderNotConfiguredError,
    InvalidStateError,
    OAuthProviderError,
)

User = get_user_model()


@pytest.mark.django_db
class TestOAuthService:
    """OAuthService.login flow with mocked provider and callables."""

    @patch("company_sso_core.services.oauth_service.get_provider")
    @patch("company_sso_core.services.oauth_service.get_provider_credentials")
    def test_login_success_returns_user_and_tokens(
        self, mock_get_creds, mock_get_provider
    ):
        """When provider returns token and user_info, login returns user and tokens."""
        mock_get_creds.return_value = {
            "client_id": "cid",
            "client_secret": "csec",
            "extra_config": {},
        }
        mock_provider = MagicMock()
        mock_provider.exchange_code.return_value = {"access_token": "at"}
        mock_provider.get_user_info.return_value = {
            "id": "1",
            "email": "u@test.com",
            "name": "User",
        }
        mock_get_provider.return_value = mock_provider

        service = OAuthService()
        user, tokens = service.login(
            provider_slug="google",
            code="code",
            redirect_uri="https://app.com/cb",
            request=None,
        )
        assert user is not None
        assert user.email == "u@test.com"
        assert tokens["access"] == f"access_{user.pk}"
        assert tokens["refresh"] == f"refresh_{user.pk}"
        log = SSOLoginLog.objects.filter(provider_slug="google", status="success").first()
        assert log is not None
        assert log.user == user

    @patch("company_sso_core.services.oauth_service.get_provider_credentials")
    def test_login_raises_when_provider_disabled(self, mock_get_creds):
        """When SocialProvider exists and is_active=False, raise ProviderDisabledError."""
        from company_sso_core.models import SocialProvider
        SocialProvider.objects.create(
            slug="google",
            name="Google",
            client_id="x",
            client_secret="y",
            is_active=False,
            workspace_id=None,
        )
        service = OAuthService()
        with pytest.raises(ProviderDisabledError):
            service.login(
                provider_slug="google",
                code="code",
                redirect_uri="https://app.com/cb",
                request=None,
            )
        mock_get_creds.assert_not_called()

    @patch("company_sso_core.services.oauth_service._validate_state_callable")
    @patch("company_sso_core.services.oauth_service.get_provider")
    @patch("company_sso_core.services.oauth_service.get_provider_credentials")
    def test_login_validates_state_when_callable_set(
        self, mock_get_creds, mock_get_provider, mock_validate_state
    ):
        """When SSO_VALIDATE_STATE returns False, raise InvalidStateError."""
        mock_validate_state.return_value = lambda state, req: False
        mock_get_creds.return_value = {"client_id": "x", "client_secret": "y"}
        mock_get_provider.return_value = MagicMock()
        service = OAuthService()
        with pytest.raises(InvalidStateError):
            service.login(
                provider_slug="google",
                code="code",
                redirect_uri="https://app.com/cb",
                state="wrong_state",
                request=None,
            )
