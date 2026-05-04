"""
Request/response serializers for SSO API. Validation only.
"""
from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers


@extend_schema_serializer(component_name="SSOLoginRequestBody")
class SSOLoginSerializer(serializers.Serializer):
    """Request body for POST login/<provider>/. Redirect URI is never sent here—use ``SSO_REDIRECT_URI`` in settings."""

    code = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="Authorization code from the OAuth provider callback (`?code=...`).",
    )
    workspace_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Optional. Workspace id when using workspace-scoped `SocialProvider` rows.",
    )
    state = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional CSRF token; validated with `SSO_VALIDATE_STATE` when configured.",
    )
