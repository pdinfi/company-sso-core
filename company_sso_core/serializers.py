"""
Request/response serializers for SSO API. Validation only.
"""
from rest_framework import serializers


class SSOLoginSerializer(serializers.Serializer):
    """Request body for POST login/<provider>/."""

    code = serializers.CharField(required=True, allow_blank=False)
    workspace_id = serializers.IntegerField(required=False, allow_null=True)
    state = serializers.CharField(required=False, allow_blank=True)
    redirect_uri = serializers.URLField(required=False, allow_blank=True)
