# company-sso-core

Production-grade reusable Django SSO package for OAuth2 login with **Google**, **GitHub**, and **Facebook**. Supports credential loading from database (primary), Django settings, or environment variables; provider registry with auto-registration; state validation; and JWT issuance via configurable callables.

## Installation

```bash
pip install git+https://github.com/org/company-sso-core.git
```

Or from a local path:

```bash
pip install -e /path/to/company-sso-core
```

### Virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

## Add to your Django project

1. **INSTALLED_APPS** (in `settings.py`):

   ```python
   INSTALLED_APPS = [
       # ...
       "rest_framework",
       "drf_spectacular",
       "company_sso_core",
   ]
   ```

2. **Include URLs** (in your root `urls.py`):

   ```python
   from django.urls import path, include

   urlpatterns = [
       path("api/v1/sso/", include("company_sso_core.urls")),
       # Optional: Swagger
       # path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
       # path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
   ]
   ```

3. **Run migrations**

   ```bash
   python manage.py migrate
   ```

4. **Configure settings** (see below).

## Required settings

| Setting | Description |
|--------|-------------|
| `SSO_GET_OR_CREATE_USER` | Callable `(provider_slug, user_info_dict, request) -> (user, created)`. Resolves or creates the Django user after OAuth. |
| `SSO_ISSUE_TOKENS` | Callable `(user, request) -> dict`. Returns e.g. `{"access": "...", "refresh": "..."}` for JWT (or any token format). |

Optional:

| Setting | Description |
|--------|-------------|
| `SSO_PROVIDERS` | Fallback credentials: `{"google": {"client_id": "...", "client_secret": "..."}, ...}`. Host can use `os.getenv("GOOGLE_CLIENT_ID")` etc. |
| `SSO_VALIDATE_STATE` | Callable `(state, request) -> bool`. Validate OAuth state parameter; return False or raise to reject. |

## Credential resolution order

1. **Database**: `SocialProvider` with matching `slug` and optional `workspace_id`, `is_active=True`.
2. **Settings**: `settings.SSO_PROVIDERS[provider_slug]`.
3. If not found: `ProviderNotConfiguredError` (400).

Secrets are never logged or exposed in API responses.

## API

### POST `/api/v1/sso/login/<provider>/`

Exchange an OAuth authorization code for tokens and optionally create/get user.

**Request body:**

```json
{
  "code": "authorization_code_from_provider",
  "workspace_id": 1,
  "state": "optional_state_for_csrf",
  "redirect_uri": "https://yourapp.com/callback"
}
```

- `code` (required): Authorization code from the OAuth provider.
- `workspace_id` (optional): For workspace-scoped provider credentials.
- `state` (optional): Validated by `SSO_VALIDATE_STATE` if set.
- `redirect_uri` (optional): Must match the redirect URI used in the authorization request.

**Responses:**

- **200**: `{"access": "...", "refresh": "...", "user": {"id": 1, "email": "..."}}` (shape depends on `SSO_ISSUE_TOKENS` and your serialization).
- **400**: Validation error, invalid state, or provider not configured.
- **403**: Provider disabled (`is_active=False`).
- **502**: OAuth provider error (token/user_info exchange failed).

## Example settings (host project)

```python
import os

# Fallback credentials (e.g. from env)
SSO_PROVIDERS = {
    "google": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
    },
}

def get_or_create_sso_user(provider_slug, user_info, request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    email = user_info.get("email")
    if not email:
        return None, False
    user, created = User.objects.get_or_create(
        username=email,
        defaults={"email": email, "first_name": user_info.get("name", "").split()[0] or "", "last_name": "".join(user_info.get("name", "").split()[1:])},
    )
    return user, created

def issue_sso_tokens(user, request):
    # Example: use djangorestframework-simplejwt
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}

SSO_GET_OR_CREATE_USER = get_or_create_sso_user
SSO_ISSUE_TOKENS = issue_sso_tokens
```

## Admin

- **SocialProvider**: Enable/disable providers, manage `client_id` / `client_secret` (secret is masked in the admin), set `workspace_id` and `extra_config`.
- **SSOLoginLog**: View login attempts (provider, user, status, IP, created_at); filter by status and provider.

## Security

- Validate state via `SSO_VALIDATE_STATE` when using state parameter.
- Client secrets are never logged; masked in admin.
- Disabled providers return 403 before any token exchange.

## Tests

From the project that has `company_sso_core` in `INSTALLED_APPS`:

```bash
python manage.py test company_sso_core
```

Or with pytest (from package root):

```bash
pytest tests/
```

Set `DJANGO_SETTINGS_MODULE=tests.settings` when running tests from the package root.
