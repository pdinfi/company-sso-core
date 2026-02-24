"""Custom exceptions; map to proper HTTP status codes in views."""
from rest_framework.exceptions import APIException
from rest_framework import status


class SSOException(APIException):
    """Base for SSO-related exceptions."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "An SSO error occurred."
    default_code = "sso_error"


class ProviderNotConfiguredError(SSOException):
    """Provider not found in DB or settings."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "SSO provider is not configured."
    default_code = "provider_not_configured"


class ProviderDisabledError(SSOException):
    """Provider exists but is disabled (is_active=False)."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "This SSO provider is disabled."
    default_code = "provider_disabled"


class InvalidStateError(SSOException):
    """OAuth state parameter invalid or expired."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid or expired state parameter."
    default_code = "invalid_state"


class OAuthProviderError(SSOException):
    """Token or user_info exchange failed with the OAuth provider."""

    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "OAuth provider error. Please try again later."
    default_code = "oauth_provider_error"
