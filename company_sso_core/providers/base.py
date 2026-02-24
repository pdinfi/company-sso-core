"""
Base OAuth provider (Strategy pattern). Credentials injected via __init__; no secrets in class.
"""
from abc import ABC, ABCMeta, abstractmethod


_PROVIDER_REGISTRY: dict[str, type] = {}


class ProviderRegistryMeta(ABCMeta):
    """Metaclass that auto-registers BaseOAuthProvider subclasses by slug."""

    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        if name != "BaseOAuthProvider" and hasattr(cls, "slug") and cls.slug:
            _PROVIDER_REGISTRY[cls.slug] = cls
        return cls


class BaseOAuthProvider(ABC, metaclass=ProviderRegistryMeta):
    """
    Abstract base for all OAuth providers.
    Credentials are injected by the host via __init__; subclasses must not
    define client_id/client_secret in code.
    """

    slug: str = ""
    token_url: str = ""
    user_info_url: str = ""
    authorization_url: str = ""

    def __init__(self, credentials: dict):
        self.credentials = credentials or {}

    @abstractmethod
    def exchange_code(self, code: str, redirect_uri: str, **kwargs) -> dict:
        """
        Exchange authorization code for tokens. Return dict with at least access_token.
        """
        pass

    @abstractmethod
    def get_user_info(self, access_token: str, **kwargs) -> dict:
        """
        Fetch user info using access_token. Return normalized dict (e.g. email, id, name).
        """
        pass


def get_provider_registry():
    """Return the internal registry (for tests)."""
    return _PROVIDER_REGISTRY
