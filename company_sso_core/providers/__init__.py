"""
Provider registry: auto-registration via BaseOAuthProvider metaclass.
Import all provider modules so they register; expose get_provider(slug, credentials).
50+ SSO options: dedicated classes (google, github, facebook) + generic built-in configs.
"""
from company_sso_core.exceptions import ProviderNotConfiguredError
from company_sso_core.providers.base import BaseOAuthProvider, get_provider_registry
from company_sso_core.providers.builtin_configs import BUILTIN_OAUTH2_CONFIGS

# Import providers so they register with the metaclass.
from . import google  # noqa: F401
from . import github  # noqa: F401
from . import facebook  # noqa: F401
from . import generic  # noqa: F401


def get_provider(slug: str, credentials: dict) -> BaseOAuthProvider:
    """
    Return an OAuth provider instance for the given slug and credentials.
    Uses dedicated provider class if registered (e.g. google, github, facebook),
    otherwise GenericOAuth2Provider for any slug in BUILTIN_OAUTH2_CONFIGS (50+).
    Raises ProviderNotConfiguredError if slug is not supported.
    """
    registry = get_provider_registry()
    provider_class = registry.get(slug)
    if provider_class is not None:
        return provider_class(credentials)
    if slug in BUILTIN_OAUTH2_CONFIGS:
        from company_sso_core.providers.generic import GenericOAuth2Provider
        return GenericOAuth2Provider(credentials, slug=slug)
    raise ProviderNotConfiguredError()


def get_all_provider_slugs() -> list[str]:
    """Return all supported SSO provider slugs (dedicated + generic), sorted."""
    registry = get_provider_registry()
    dedicated = sorted(registry.keys())
    generic_slugs = sorted(BUILTIN_OAUTH2_CONFIGS.keys())
    return sorted(set(dedicated) | set(generic_slugs))


__all__ = ["BaseOAuthProvider", "get_provider", "get_provider_registry", "get_all_provider_slugs"]
