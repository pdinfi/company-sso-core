"""Admin: SocialProvider (mask client_secret) and SSOLoginLog (read-only)."""
from django.contrib import admin
from django import forms
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError

from company_sso_core.models import SocialProvider, SSOLoginLog


class SocialProviderAdminForm(forms.ModelForm):
    """Form that masks client_secret and only updates it when a new value is entered."""

    client_secret_display = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Leave blank to keep current", "autocomplete": "new-password"}),
        label="Client secret",
        help_text="Leave blank to keep the existing secret. Never displayed in full.",
    )

    class Meta:
        model = SocialProvider
        fields = [
            "slug",
            "name",
            "client_id",
            "is_active",
            "workspace_id",
            "extra_config",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.client_secret:
            self.fields["client_secret_display"].help_text = "Leave blank to keep current (stored value is masked)."
            self.fields["client_secret_display"].required = False
        else:
            self.fields["client_secret_display"].help_text = "Required when creating a new provider."
            self.fields["client_secret_display"].required = True
        self.fields["client_secret_display"].widget.attrs["placeholder"] = "********"

    def clean_client_secret_display(self):
        value = self.cleaned_data.get("client_secret_display")
        if not self.instance.pk and not value:
            raise ValidationError("Client secret is required when creating a provider.")
        return value

    def save(self, commit=True):
        obj = super().save(commit=False)
        new_secret = self.cleaned_data.get("client_secret_display")
        if new_secret:
            obj.client_secret = new_secret
        if commit:
            obj.save()
        return obj


@admin.register(SocialProvider)
class SocialProviderAdmin(admin.ModelAdmin):
    """Manage OAuth providers; client_secret is masked and never displayed."""

    form = SocialProviderAdminForm
    list_display = ("slug", "name", "is_active", "workspace_id", "created_at")
    list_filter = ("is_active",)
    search_fields = ("slug", "name")
    readonly_fields = ("created_at", "updated_at", "client_secret_masked")

    def client_secret_masked(self, obj):
        if obj and obj.client_secret:
            return mark_safe("<span style='font-family: monospace'>********</span>")
        return "—"

    client_secret_masked.short_description = "Client secret (masked)"

    def get_fieldsets(self, request, obj=None):
        return (
            (
                None,
                {
                    "fields": (
                        "slug",
                        "name",
                        "client_id",
                        "client_secret_display",
                        "is_active",
                        "workspace_id",
                        "extra_config",
                    )
                },
            ),
            ("Timestamps", {"fields": ("created_at", "updated_at")}),
        )


@admin.register(SSOLoginLog)
class SSOLoginLogAdmin(admin.ModelAdmin):
    """Read-only list of SSO login attempts."""

    list_display = ("provider_slug", "user", "status", "ip_address", "created_at")
    list_filter = ("status", "provider_slug")
    search_fields = ("user__email", "user__username", "provider_slug")
    readonly_fields = ("provider", "provider_slug", "user", "status", "ip_address", "created_at")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
