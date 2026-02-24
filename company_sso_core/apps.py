"""App config for company_sso_core."""
from django.apps import AppConfig


class CompanySsoCoreConfig(AppConfig):
    """SSO app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "company_sso_core"
    label = "company_sso_core"
    verbose_name = "Company SSO Core"

    def ready(self):
        """Import signals so they are registered."""
        try:
            import company_sso_core.signals  # noqa: F401
        except ImportError:
            pass
