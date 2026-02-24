"""
Thin API views: validate serializer, call service, return response, map exceptions to HTTP.
"""
import logging

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema, OpenApiResponse

from company_sso_core.serializers import SSOLoginSerializer
from company_sso_core.services.oauth_service import OAuthService
from company_sso_core.exceptions import (
    ProviderNotConfiguredError,
    ProviderDisabledError,
    InvalidStateError,
    OAuthProviderError,
)

logger = logging.getLogger(__name__)


@extend_schema(
    request=SSOLoginSerializer,
    responses={
        200: OpenApiResponse(description="Login success; returns tokens and optional user info"),
        400: OpenApiResponse(description="Bad Request – validation, invalid state, or provider not configured"),
        403: OpenApiResponse(description="Forbidden – provider disabled"),
        502: OpenApiResponse(description="Bad Gateway – OAuth provider error"),
    },
)
class SSOLoginView(APIView):
    """POST login/<provider>/ – exchange OAuth code for tokens."""

    permission_classes = []
    authentication_classes = []

    def post(self, request: Request, provider: str):
        serializer = SSOLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        code = data["code"]
        workspace_id = data.get("workspace_id")
        state = data.get("state") or None
        redirect_uri = data.get("redirect_uri") or ""

        try:
            service = OAuthService()
            user, tokens = service.login(
                provider_slug=provider,
                code=code,
                redirect_uri=redirect_uri,
                workspace=workspace_id,
                state=state,
                request=request,
            )
        except ProviderDisabledError as e:
            return Response(
                {"detail": e.detail, "code": e.default_code},
                status=status.HTTP_403_FORBIDDEN,
            )
        except (ProviderNotConfiguredError, InvalidStateError) as e:
            return Response(
                {"detail": e.detail, "code": e.default_code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except OAuthProviderError as e:
            logger.warning("OAuth provider error: %s", e.detail)
            return Response(
                {"detail": e.detail or "OAuth provider error.", "code": e.default_code},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            logger.exception("SSO login error: %s", e)
            return Response(
                {"detail": "An error occurred. Please try again later.", "code": "error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_data = dict(tokens)
        if user:
            response_data["user"] = {
                "id": user.pk,
                "email": getattr(user, "email", None) or "",
                "username": getattr(user, "username", None) or "",
            }
        return Response(response_data, status=status.HTTP_200_OK)
