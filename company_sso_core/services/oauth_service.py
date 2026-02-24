"""
OAuth login orchestration: credentials, exchange code, user resolution, tokens, logging.
Never log client_secret or tokens.
"""
import logging

from django.conf import settings
from django.utils.module_loading import import_string

from company_sso_core.models import SocialProvider, SSOLoginLog
from company_sso_core.exceptions import (
    ProviderNotConfiguredError,
    ProviderDisabledError,
    InvalidStateError,
    OAuthProviderError,
)
from company_sso_core.services.credential_loader import get_provider_credentials
from company_sso_core.providers import get_provider
from company_sso_core.utils import get_setting, get_client_ip

logger = logging.getLogger(__name__)


def _get_or_create_user_callable():
    """Resolve SSO_GET_OR_CREATE_USER from settings (callable or dotted path)."""
    fn = get_setting("SSO_GET_OR_CREATE_USER")
    if fn is None:
        raise ProviderNotConfiguredError(detail="SSO_GET_OR_CREATE_USER is not configured")
    if isinstance(fn, str):
        return import_string(fn)
    return fn


def _issue_tokens_callable():
    """Resolve SSO_ISSUE_TOKENS from settings (callable or dotted path)."""
    fn = get_setting("SSO_ISSUE_TOKENS")
    if fn is None:
        raise ProviderNotConfiguredError(detail="SSO_ISSUE_TOKENS is not configured")
    if isinstance(fn, str):
        return import_string(fn)
    return fn


def _validate_state_callable():
    """Optional SSO_VALIDATE_STATE callable."""
    fn = get_setting("SSO_VALIDATE_STATE")
    if fn is None:
        return None
    if isinstance(fn, str):
        return import_string(fn)
    return fn


def _check_provider_disabled(provider_slug: str, workspace=None) -> None:
    """If a SocialProvider exists for this slug/workspace and is inactive, raise ProviderDisabledError."""
    qs = SocialProvider.objects.filter(slug=provider_slug)
    if workspace is not None:
        qs = qs.filter(workspace_id=workspace)
    else:
        qs = qs.filter(workspace_id__isnull=True)
    provider = qs.first()
    if provider and not provider.is_active:
        raise ProviderDisabledError()


class OAuthService:
    """
    Orchestrates SSO login: load credentials, exchange code, get user info,
    get-or-create user, issue tokens, log attempt. Credentials and tokens are never logged.
    """

    def login(
        self,
        provider_slug: str,
        code: str,
        redirect_uri: str,
        workspace=None,
        state: str = None,
        request=None,
    ) -> tuple:
        """
        Perform OAuth login. Returns (user, tokens_dict).
        Raises ProviderDisabledError, ProviderNotConfiguredError, InvalidStateError, OAuthProviderError.
        """
        _check_provider_disabled(provider_slug, workspace)
        credentials = get_provider_credentials(provider_slug, workspace)
        provider_instance = get_provider(provider_slug, credentials)

        validate_state = _validate_state_callable()
        if validate_state is not None and state is not None:
            if not validate_state(state, request):
                raise InvalidStateError()

        try:
            token_response = provider_instance.exchange_code(code, redirect_uri=redirect_uri)
        except Exception as e:
            self._log_attempt(provider_slug, None, "failed", request, workspace=workspace)
            raise OAuthProviderError(detail=str(e) if getattr(e, "args", None) else "Token exchange failed")

        access_token = token_response.get("access_token")
        if not access_token:
            self._log_attempt(provider_slug, None, "failed", request, workspace=workspace)
            raise OAuthProviderError(detail="No access_token in response")

        try:
            user_info = provider_instance.get_user_info(access_token)
        except Exception as e:
            self._log_attempt(provider_slug, None, "failed", request, workspace=workspace)
            raise OAuthProviderError(detail=str(e) if getattr(e, "args", None) else "User info fetch failed")

        get_or_create_user = _get_or_create_user_callable()
        try:
            user, created = get_or_create_user(provider_slug, user_info, request)
        except Exception as e:
            self._log_attempt(provider_slug, None, "failed", request, workspace=workspace)
            logger.exception("SSO get_or_create_user failed: %s", e)
            raise OAuthProviderError(detail="User resolution failed")

        if user is None:
            self._log_attempt(provider_slug, None, "failed", request, workspace=None)
            raise OAuthProviderError(detail="User could not be resolved")

        issue_tokens = _issue_tokens_callable()
        try:
            tokens = issue_tokens(user, request)
        except Exception as e:
            self._log_attempt(provider_slug, user, "failed", request, workspace=workspace)
            logger.exception("SSO issue_tokens failed: %s", e)
            raise OAuthProviderError(detail="Token issuance failed")

        self._log_attempt(provider_slug, user, "success", request, workspace=workspace)
        return user, tokens

    def _log_attempt(
        self,
        provider_slug: str,
        user,
        status: str,
        request,
        workspace=None,
    ):
        """Create SSOLoginLog; never log secrets."""
        ip = get_client_ip(request) if request else None
        qs = SocialProvider.objects.filter(slug=provider_slug, is_active=True)
        if workspace is not None:
            qs = qs.filter(workspace_id=workspace)
        else:
            qs = qs.filter(workspace_id__isnull=True)
        provider_model = qs.first()
        SSOLoginLog.objects.create(
            provider=provider_model,
            provider_slug=provider_slug,
            user=user,
            status=status,
            ip_address=ip,
        )
