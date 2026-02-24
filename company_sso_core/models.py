"""SSO models: SocialProvider and SSOLoginLog."""
from django.conf import settings
from django.db import models


class SocialProvider(models.Model):
    """
    OAuth provider configuration. Credentials stored here or fallback to settings.
    workspace_id null means global provider.
    """

    slug = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True, db_index=True)
    workspace_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    extra_config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["slug"]
        indexes = [
            models.Index(fields=["slug", "workspace_id"]),
            models.Index(fields=["is_active"]),
        ]
        verbose_name = "Social provider"
        verbose_name_plural = "Social providers"

    def __str__(self):
        return f"{self.name} ({self.slug})"


class SSOLoginLog(models.Model):
    """Log of SSO login attempts (success or failed)."""

    class Status(models.TextChoices):
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    provider = models.ForeignKey(
        SocialProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_logs",
        db_index=True,
    )
    provider_slug = models.CharField(max_length=50, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sso_login_logs",
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        db_index=True,
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["provider_slug", "status"]),
            models.Index(fields=["created_at"]),
        ]
        verbose_name = "SSO login log"
        verbose_name_plural = "SSO login logs"

    def __str__(self):
        return f"{self.provider_slug} {self.status} at {self.created_at}"
