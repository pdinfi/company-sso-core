"""
Minimal Django settings for running tests. Set DJANGO_SETTINGS_MODULE=tests.settings for pytest.
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

SECRET_KEY = "test-secret"
DEBUG = True
USE_TZ = True
AUTH_USER_MODEL = "auth.User"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "rest_framework",
    "drf_spectacular",
    "company_sso_core",
]

ROOT_URLCONF = "tests.urls"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Fallback credentials for tests
SSO_PROVIDERS = {
    "google": {
        "client_id": "test_google_client_id",
        "client_secret": "test_google_client_secret",
    },
}

# Required callables for OAuthService
def get_or_create_sso_user(provider_slug, user_info, request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    email = user_info.get("email") or f"user_{user_info.get('id', 'unknown')}@test.com"
    user, created = User.objects.get_or_create(
        username=email,
        defaults={"email": email},
    )
    return user, created


def issue_sso_tokens(user, request):
    return {"access": f"access_{user.pk}", "refresh": f"refresh_{user.pk}"}


SSO_GET_OR_CREATE_USER = get_or_create_sso_user
SSO_ISSUE_TOKENS = issue_sso_tokens
