"""Shared utilities; no business logic. Settings and request helpers."""
import logging
from urllib.parse import urlencode

from django.conf import settings

logger = logging.getLogger(__name__)


def get_authorization_url(
    provider_slug: str,
    redirect_uri: str,
    state: str | None = None,
    scope: str | None = None,
    workspace: int | None = None,
) -> str:
    """
    Build the OAuth2 authorization URL for the given provider. Use this to redirect
    users to the provider's sign-in page.

    Uses the same credential resolution as login (DB then SSO_PROVIDERS).
    Resolves placeholders in URLs (e.g. {domain} for Okta) from extra_config.

    :param provider_slug: e.g. "google", "microsoft", "linkedin"
    :param redirect_uri: Must match the callback URL registered with the provider
    :param state: Optional CSRF state (recommended)
    :param scope: Optional scope string; default "openid email profile"
    :param workspace: Optional workspace_id for workspace-scoped credentials
    :returns: Full URL to redirect the user to
    :raises: ProviderNotConfiguredError if provider not configured
    """
    from company_sso_core.services.credential_loader import get_provider_credentials
    from company_sso_core.providers import get_provider

    creds = get_provider_credentials(provider_slug, workspace)
    provider = get_provider(provider_slug, creds)
    base_url = (provider.authorization_url or "").strip()
    if not base_url:
        raise ValueError(f"Provider {provider_slug} has no authorization_url")
    extra = creds.get("extra_config") or {}
    for key, value in extra.items():
        if value and "{" + key + "}" in base_url:
            base_url = base_url.replace("{" + key + "}", str(value).strip("/"))
    params = {
        "client_id": creds["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope or "openid email profile",
    }
    if state:
        params["state"] = state
    sep = "&" if "?" in base_url else "?"
    return base_url + sep + urlencode(params)


def get_setting(name: str, default=None):
    """
    Read optional SSO setting from Django settings.
    """
    return getattr(settings, name, default)


def get_client_ip(request) -> str | None:
    """Get client IP from request; safe for logging (no secrets)."""
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
