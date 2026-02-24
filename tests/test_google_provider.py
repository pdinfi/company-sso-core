"""Tests for Google OAuth provider: exchange_code and get_user_info (mocked)."""
import pytest
from unittest.mock import patch, MagicMock

from company_sso_core.providers.google import GoogleOAuthProvider


class TestGoogleOAuthProvider:
    """Google provider uses token_url and user_info_url; no credentials in class."""

    @patch("company_sso_core.providers.google.requests.post")
    def test_exchange_code_returns_tokens(self, mock_post):
        """exchange_code POSTs to token_url and returns JSON with access_token."""
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"access_token": "ya29.xxx", "expires_in": 3599, "token_type": "Bearer"},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        provider = GoogleOAuthProvider({"client_id": "cid", "client_secret": "csec"})
        out = provider.exchange_code("auth_code", "https://app.com/callback")
        assert out["access_token"] == "ya29.xxx"
        mock_post.assert_called_once()
        call_kw = mock_post.call_args[1]
        assert call_kw.get("data", {}).get("code") == "auth_code"

    @patch("company_sso_core.providers.google.requests.get")
    def test_get_user_info_returns_normalized(self, mock_get):
        """get_user_info GETs userinfo and returns id, email, name, picture."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "id": "123",
                "email": "u@example.com",
                "name": "Test User",
                "picture": "https://photo",
            },
        )
        mock_get.return_value.raise_for_status = MagicMock()
        provider = GoogleOAuthProvider({})
        out = provider.get_user_info("ya29.xxx")
        assert out["id"] == "123"
        assert out["email"] == "u@example.com"
        assert out["name"] == "Test User"
        assert out["picture"] == "https://photo"

    def test_exchange_code_raises_on_missing_credentials(self):
        """Missing client_id or client_secret raises OAuthProviderError."""
        from company_sso_core.exceptions import OAuthProviderError
        provider = GoogleOAuthProvider({"client_id": "", "client_secret": "x"})
        with pytest.raises(OAuthProviderError):
            provider.exchange_code("code", "https://x.com/cb")
