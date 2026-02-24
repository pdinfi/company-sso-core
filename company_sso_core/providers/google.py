"""
Google OAuth2 provider. Credentials (client_id, client_secret) injected via __init__.
"""
import requests

from company_sso_core.exceptions import OAuthProviderError
from company_sso_core.providers.base import BaseOAuthProvider


class GoogleOAuthProvider(BaseOAuthProvider):
    """Google OAuth2; credentials injected via __init__(credentials)."""

    slug = "google"
    token_url = "https://oauth2.googleapis.com/token"
    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    authorization_url = "https://accounts.google.com/o/oauth2/v2/auth"

    def exchange_code(self, code: str, redirect_uri: str, **kwargs) -> dict:
        """Exchange authorization code for tokens."""
        client_id = self.credentials.get("client_id")
        client_secret = self.credentials.get("client_secret")
        if not client_id or not client_secret:
            raise OAuthProviderError(detail="Missing Google client_id or client_secret")
        data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        resp = requests.post(
            self.token_url,
            data=data,
            headers={"Accept": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_user_info(self, access_token: str, **kwargs) -> dict:
        """Fetch user info from Google."""
        resp = requests.get(
            self.user_info_url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "id": data.get("id"),
            "email": data.get("email"),
            "name": data.get("name", ""),
            "picture": data.get("picture"),
        }
