"""Shared utilities; no business logic. Settings and request helpers."""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


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
