"""
Facebook OAuth2 provider. Credentials injected via __init__. Placeholder implementation.
"""
import requests

from company_sso_core.exceptions import OAuthProviderError
from company_sso_core.providers.base import BaseOAuthProvider


class FacebookOAuthProvider(BaseOAuthProvider):
    """Facebook OAuth2; credentials injected via __init__(credentials)."""

    slug = "facebook"
    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
    user_info_url = "https://graph.facebook.com/me"
    authorization_url = "https://www.facebook.com/v18.0/dialog/oauth"

    def exchange_code(self, code: str, redirect_uri: str, **kwargs) -> dict:
        """Exchange authorization code for tokens."""
        client_id = self.credentials.get("client_id")
        client_secret = self.credentials.get("client_secret")
        if not client_id or not client_secret:
            raise OAuthProviderError(detail="Missing Facebook client_id or client_secret")
        params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        }
        resp = requests.get(self.token_url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_user_info(self, access_token: str, **kwargs) -> dict:
        """Fetch user info from Facebook."""
        resp = requests.get(
            self.user_info_url,
            params={"fields": "id,name,email,picture"},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        picture = None
        if data.get("picture", {}).get("data", {}).get("url"):
            picture = data["picture"]["data"]["url"]
        return {
            "id": str(data.get("id", "")),
            "email": data.get("email", ""),
            "name": data.get("name", ""),
            "picture": picture,
        }
