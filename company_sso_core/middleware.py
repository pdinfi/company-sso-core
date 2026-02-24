"""
Optional middleware for SSO. Kept minimal so host can extend.
Example: inject request.workspace from header for workspace-scoped credentials.
"""
from company_sso_core.utils import get_setting


class SSOWorkspaceMiddleware:
    """
    If SSO_WORKSPACE_HEADER is set (e.g. "X-Workspace-Id"), set request.workspace_id
    from that header for use in credential resolution.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        header_name = get_setting("SSO_WORKSPACE_HEADER")
        if header_name:
            value = request.META.get(f"HTTP_{header_name.upper().replace('-', '_')}")
            if value is not None:
                try:
                    request.workspace_id = int(value)
                except (ValueError, TypeError):
                    request.workspace_id = None
        else:
            request.workspace_id = getattr(request, "workspace_id", None)
        return self.get_response(request)
