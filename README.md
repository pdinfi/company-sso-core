# company-sso-core

Production-grade reusable Django SSO package for OAuth2 login with **50+ providers** (e.g. Google, GitHub, Facebook, Microsoft, Apple, LinkedIn, Slack, Discord, GitLab, Okta, Auth0, and many more). Supports credential loading from database (primary), Django settings, or environment variables; provider registry with auto-registration; generic OAuth2/OIDC configs for built-in providers; state validation; and JWT issuance via configurable callables.

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

## Supported SSO providers (50+)

The package supports **69** provider slugs:

- **Dedicated implementations**: `google`, `github`, `facebook` (custom token/userinfo handling).
- **Generic OAuth2/OIDC** (built-in configs): `microsoft`, `apple`, `twitter`, `linkedin`, `amazon`, `discord`, `slack`, `spotify`, `yahoo`, `gitlab`, `bitbucket`, `dropbox`, `box`, `paypal`, `twitch`, `reddit`, `tumblr`, `meetup`, `patreon`, `pinterest`, `salesforce`, `zendesk`, `atlassian`, `notion`, `figma`, `linear`, `vercel`, `digitalocean`, `heroku`, `zoom`, `adobe`, `dribbble`, `strava`, `soundcloud`, `trello`, `asana`, `yandex`, `mailru`, `vk`, `weibo`, `okta`, `auth0`, `keycloak`, `instagram`, `snapchat`, `tiktok`, `evernote`, `fitbit`, `lastfm`, `medium`, `wordpress`, `deviantart`, `stackoverflow`, `imgur`, `foursquare`, `goodreads`, `buffer`, `podio`, `basecamp`, `xero`, `hubspot`, `mailchimp`, `shopify`, `quickbooks`, `stripe`, `twilio`, `openid`, and others.

To list all slugs programmatically:

```python
from company_sso_core.providers import get_all_provider_slugs
slugs = get_all_provider_slugs()  # sorted list of all supported provider slugs
```

For providers that require a **tenant/domain** (e.g. Okta, Auth0, Keycloak, Zendesk, Shopify), set `extra_config` in the database (`SocialProvider.extra_config`) or in `SSO_PROVIDERS` with keys such as `domain`, `realm_url`, or `subdomain` so the generic provider can build the correct token/userinfo URLs.

## How to connect other providers and use them

### 1. Connect a provider (choose one)

**Option A – Django Admin (recommended for production)**  
- Go to **SocialProvider** in admin, add a record: set **slug** (e.g. `microsoft`, `linkedin`), **client_id**, **client_secret**, leave **workspace** blank for global (or set for workspace-specific credentials).  
- For Okta/Auth0/Keycloak/Zendesk/Shopify, set **extra_config** JSON, e.g. `{"domain": "https://your-tenant.okta.com"}` or `{"realm_url": "https://auth.example.com/realms/my-realm"}` or `{"subdomain": "yoursubdomain"}` for Zendesk, or `{"shop": "mystore"}` for Shopify.

**Option B – Settings fallback**  
- In `settings.py`, add the provider to `SSO_PROVIDERS` with `client_id`, `client_secret`, and optionally `extra_config`:

```python
SSO_PROVIDERS = {
    "linkedin": {
        "client_id": os.getenv("LINKEDIN_CLIENT_ID"),
        "client_secret": os.getenv("LINKEDIN_CLIENT_SECRET"),
    },
    "okta": {
        "client_id": os.getenv("OKTA_CLIENT_ID"),
        "client_secret": os.getenv("OKTA_CLIENT_SECRET"),
        "extra_config": {"domain": "https://your-tenant.okta.com"},
    },
}
```

Register the app and create OAuth2 credentials in each provider’s developer console. Set **`SSO_REDIRECT_URI`** in Django settings (usually from `.env`) to the **exact** callback URL you register with providers; the server uses it for both the authorization request and the code exchange—clients must not send `redirect_uri`.

### 2. How to use (SSO flow)

1. **Set `SSO_REDIRECT_URI`** in settings to your callback, e.g. `SSO_REDIRECT_URI = os.environ["SSO_REDIRECT_URI"]` (must match what you registered at the OAuth provider).

2. **Get the authorization URL** (redirect your user to the provider’s sign-in page). `get_authorization_url` uses `SSO_REDIRECT_URI` automatically:

   ```python
   from company_sso_core.utils import get_authorization_url

   state = "random_csrf_token"  # generate and validate via SSO_VALIDATE_STATE
   url = get_authorization_url("linkedin", state=state)
   # Optional: scope="r_liteprofile r_emailaddress" for LinkedIn, e.g. get_authorization_url("linkedin", state=state, scope="...")
   # Redirect the user to `url` (e.g. 302 or frontend window.location).
   ```

3. **User signs in** at the provider; the provider redirects to your configured callback URL with `?code=...&state=...`.

4. **Exchange the code for tokens** — the backend reads `redirect_uri` only from settings, not from the request body:

   ```http
   POST /api/v1/sso/login/linkedin/
   Content-Type: application/json

   {"code": "auth_code_from_callback", "state": "random_csrf_token"}
   ```

5. **Response** (200): `{"access": "...", "refresh": "...", "user": {"id": 1, "email": "..."}}` — use the tokens for authenticated requests.

Frontend example: your backend can expose an endpoint that returns the authorization URL (`get_authorization_url("linkedin", state=state)`); the login page redirects to that URL. After the callback, POST only `code` and optional `state` to `POST .../login/<provider>/`.

## Required settings

| Setting | Description |
|--------|-------------|
| `SSO_GET_OR_CREATE_USER` | Callable `(provider_slug, user_info_dict, request) -> (user, created)`. Resolves or creates the Django user after OAuth. |
| `SSO_ISSUE_TOKENS` | Callable `(user, request) -> dict`. Returns e.g. `{"access": "...", "refresh": "..."}` for JWT (or any token format). |
| `SSO_REDIRECT_URI` | Full callback URL for OAuth (e.g. `https://yourapp.com/api/v1/sso/callback`). Must match what you register at each provider; set from environment (`os.environ`). Used for token exchange and for `get_authorization_url`; **never** taken from client input. |

Optional:

| Setting | Description |
|--------|-------------|
| `SSO_PROVIDERS` | Fallback credentials: `{"google": {"client_id": "...", "client_secret": "..."}, "microsoft": {...}, ...}`. Any supported provider slug (see above). Use `os.getenv(...)` for secrets. For Okta/Auth0/Keycloak etc., include `extra_config`: e.g. `{"domain": "https://your-tenant.okta.com"}`. |
| `SSO_VALIDATE_STATE` | Callable `(state, request) -> bool`. Validate OAuth state parameter; return False or raise to reject. |

## Credential resolution order

1. **Database**: `SocialProvider` with matching `slug` and optional `workspace_id`, `is_active=True`.
2. **Settings**: `settings.SSO_PROVIDERS[provider_slug]`.
3. If not found: `ProviderNotConfiguredError` (400).

Secrets are never logged or exposed in API responses.

## OpenAPI / Swagger (drf-spectacular)

- Request body fields are **`code`**, optional **`state`**, optional **`workspace_id`**. There is **no `redirect_uri`** in the API; set **`SSO_REDIRECT_URI`** in settings (see above).
- If Swagger UI still shows an old schema, restart the app and hard-refresh the docs page (or open the raw schema at `/api/schema/` and confirm `SSOLoginRequestBody`).
- **“JSON parse error”** in Swagger almost always means the request body is not valid JSON: use **double quotes** for keys and strings, **no trailing commas**, and **no** `//` or `#` comments. Copy the **Examples** from Swagger rather than pasting from Python dicts or README if you edit the payload by hand.

## API

### POST `/api/v1/sso/login/<provider>/`

Exchange an OAuth authorization code for tokens and optionally create/get user. `<provider>` is any supported slug (e.g. `google`, `github`, `microsoft`, `linkedin`—see **Supported SSO providers** above).

**Request body:**

```json
{
  "code": "authorization_code_from_provider",
  "workspace_id": 1,
  "state": "optional_state_for_csrf"
}
```

- `code` (required): Authorization code from the OAuth provider.
- `workspace_id` (optional): For workspace-scoped provider credentials.
- `state` (optional): Validated by `SSO_VALIDATE_STATE` if set.

The **redirect URI** is always **`SSO_REDIRECT_URI`** from Django settings (typically loaded from `.env`). Do not pass it in the request body.

**Responses:**

- **200**: `{"access": "...", "refresh": "...", "user": {"id": 1, "email": "..."}}` (shape depends on `SSO_ISSUE_TOKENS` and your serialization).
- **400**: Validation error, invalid state, or provider not configured.
- **403**: Provider disabled (`is_active=False`).
- **502**: OAuth provider error (token/user_info exchange failed).

## Example settings (host project)

```python
import os

# Required: same URL registered in Google / OAuth app dashboards
SSO_REDIRECT_URI = os.environ.get("SSO_REDIRECT_URI", "https://yourapp.com/api/v1/sso/callback")

# Fallback credentials (e.g. from env). Use any supported provider slug (50+).
SSO_PROVIDERS = {
    "google": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
    },
    "microsoft": {
        "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
        "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET"),
    },
    # Okta / Auth0 / Keycloak need extra_config for tenant URLs, e.g.:
    # "okta": {"client_id": "...", "client_secret": "...", "extra_config": {"domain": "https://your-tenant.okta.com"}},
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
