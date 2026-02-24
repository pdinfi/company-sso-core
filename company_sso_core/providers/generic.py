"""
Generic OAuth2 provider: works with any OAuth2/OIDC provider via built-in configs.
Used when no dedicated provider class exists; supports 50+ built-in slugs.
"""
import re
import requests

from company_sso_core.exceptions import OAuthProviderError
from company_sso_core.providers.base import BaseOAuthProvider
from company_sso_core.providers.builtin_configs import BUILTIN_OAUTH2_CONFIGS


def _get_nested(data: dict, path: str):
    """Get value from dict by key or dot path, e.g. 'data.attributes.email' or 'items[0].id'."""
    if not path or not data:
        return None
    parts = re.split(r"\.|\[|\]", path)
    parts = [p for p in parts if p]
    for part in parts:
        if part.isdigit():
            try:
                data = data[int(part)]
            except (IndexError, KeyError, TypeError):
                return None
        else:
            data = (data or {}).get(part)
    return data


class GenericOAuth2Provider(BaseOAuthProvider):
    """
    Generic OAuth2 provider driven by built-in config (token_url, user_info_url, authorization_url).
    Not registered by slug in the metaclass; get_provider() instantiates it for any slug
    present in BUILTIN_OAUTH2_CONFIGS when no dedicated provider exists.
    """

    slug = ""  # Not registered via metaclass; used per-call via get_provider(slug, creds)

    def __init__(self, credentials: dict, slug: str = ""):
        super().__init__(credentials)
        self._slug = (slug or (credentials.get("_provider_slug") or "")).strip()
        if not self._slug or self._slug not in BUILTIN_OAUTH2_CONFIGS:
            raise OAuthProviderError(detail=f"Unknown or unsupported generic provider: {self._slug!r}")
        self._config = BUILTIN_OAUTH2_CONFIGS[self._slug].copy()
        extra = (credentials.get("extra_config") or {}).copy()
        # Allow extra_config to override endpoints (e.g. Okta domain, Keycloak realm)
        for key in ("token_url", "user_info_url", "authorization_url"):
            if key in extra and extra[key]:
                self._config[key] = extra[key]
        self.token_url = self._config.get("token_url") or ""
        self.user_info_url = self._config.get("user_info_url") or ""
        self.authorization_url = self._config.get("authorization_url") or ""

    @property
    def slug(self) -> str:
        return self._slug

    def exchange_code(self, code: str, redirect_uri: str, **kwargs) -> dict:
        """Exchange authorization code for tokens (standard OAuth2 POST)."""
        client_id = self.credentials.get("client_id")
        client_secret = self.credentials.get("client_secret")
        if not client_id or not client_secret:
            raise OAuthProviderError(detail=f"Missing client_id or client_secret for {self._slug}")
        token_url = self._resolve_url(self.token_url)
        if not token_url:
            raise OAuthProviderError(detail=f"Missing token_url for {self._slug}")
        data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        resp = requests.post(
            token_url,
            data=data,
            headers={"Accept": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_user_info(self, access_token: str, **kwargs) -> dict:
        """Fetch user info and normalize to id, email, name, picture."""
        user_info_url = self._resolve_url(self.user_info_url)
        if not user_info_url:
            return {"id": None, "email": "", "name": "", "picture": None}
        resp = requests.get(
            user_info_url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        # Some APIs wrap in "data", "response", or "user"
        if isinstance(data, dict) and "data" in data:
            inner = data["data"]
            if isinstance(inner, list) and inner and isinstance(inner[0], dict):
                data = inner[0]
            elif isinstance(inner, dict):
                data = inner
        if isinstance(data, dict) and "response" in data and isinstance(data["response"], dict):
            data = data["response"]
        if isinstance(data, dict) and "user" in data:
            data = data.get("user") or data
        if isinstance(data, list) and data and isinstance(data[0], dict):
            data = data[0]
        user_map = self._config.get("user_info_map") or {}
        return {
            "id": _get_nested(data, user_map.get("id") or "id") or _get_nested(data, "sub"),
            "email": (_get_nested(data, user_map.get("email") or "email") or "") if user_map.get("email") else "",
            "name": (_get_nested(data, user_map.get("name") or "name") or "") if user_map.get("name") else "",
            "picture": _get_nested(data, user_map.get("picture") or "picture") if user_map.get("picture") else None,
        }

    def _resolve_url(self, url: str) -> str:
        """Replace placeholders like {domain}, {subdomain}, {realm_url} from extra_config."""
        if not url:
            return ""
        extra = self.credentials.get("extra_config") or {}
        for key, value in extra.items():
            if value and "{" + key + "}" in url:
                url = url.replace("{" + key + "}", str(value).strip("/"))
        return url.strip() or ""
