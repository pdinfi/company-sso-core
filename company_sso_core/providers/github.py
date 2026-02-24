"""
GitHub OAuth2 provider. Credentials injected via __init__. Placeholder implementation.
"""
import requests

from company_sso_core.exceptions import OAuthProviderError
from company_sso_core.providers.base import BaseOAuthProvider


class GitHubOAuthProvider(BaseOAuthProvider):
    """GitHub OAuth2; credentials injected via __init__(credentials)."""

    slug = "github"
    token_url = "https://github.com/login/oauth/access_token"
    user_info_url = "https://api.github.com/user"
    authorization_url = "https://github.com/login/oauth/authorize"

    def exchange_code(self, code: str, redirect_uri: str, **kwargs) -> dict:
        """Exchange authorization code for tokens."""
        client_id = self.credentials.get("client_id")
        client_secret = self.credentials.get("client_secret")
        if not client_id or not client_secret:
            raise OAuthProviderError(detail="Missing GitHub client_id or client_secret")
        data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
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
        """Fetch user info from GitHub."""
        resp = requests.get(
            self.user_info_url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        email = data.get("email")
        if not email and kwargs.get("fetch_emails"):
            em_resp = requests.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30,
            )
            if em_resp.ok and em_resp.json():
                email = next((e["email"] for e in em_resp.json() if e.get("primary")), em_resp.json()[0].get("email"))
        return {
            "id": str(data.get("id")),
            "email": email or "",
            "name": data.get("name", "") or data.get("login", ""),
            "picture": data.get("avatar_url"),
        }
