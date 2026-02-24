"""
Load OAuth provider credentials: DB (primary) then settings fallback.
Never log or expose client_secret.
"""
from django.conf import settings

from company_sso_core.models import SocialProvider
from company_sso_core.exceptions import ProviderNotConfiguredError


def get_provider_credentials(provider_slug: str, workspace=None) -> dict:
    """
    Get credentials for the given provider.
    1. If workspace provided: load workspace-specific SocialProvider (slug, workspace_id, is_active).
    2. Else: load global SocialProvider (slug, workspace_id__isnull=True, is_active).
    3. If not found: fallback to settings.SSO_PROVIDERS[provider_slug].
    4. If still not found: raise ProviderNotConfiguredError.
    Returns dict with client_id, client_secret, and optional extra_config. Never log client_secret.
    """
    qs = SocialProvider.objects.filter(slug=provider_slug, is_active=True)
    if workspace is not None:
        qs = qs.filter(workspace_id=workspace)
    else:
        qs = qs.filter(workspace_id__isnull=True)
    provider = qs.first()
    if provider:
        return {
            "client_id": provider.client_id,
            "client_secret": provider.client_secret,
            "extra_config": provider.extra_config or {},
        }
    fallback = getattr(settings, "SSO_PROVIDERS", None) or {}
    creds = fallback.get(provider_slug)
    if creds and isinstance(creds, dict):
        return {
            "client_id": creds.get("client_id", ""),
            "client_secret": creds.get("client_secret", ""),
            "extra_config": creds.get("extra_config") or {},
        }
    raise ProviderNotConfiguredError()
