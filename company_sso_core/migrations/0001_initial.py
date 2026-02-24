# Generated migration for SocialProvider and SSOLoginLog

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SocialProvider",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.CharField(db_index=True, max_length=50, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("client_id", models.CharField(max_length=255)),
                ("client_secret", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("workspace_id", models.PositiveIntegerField(blank=True, db_index=True, null=True)),
                ("extra_config", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["slug"],
                "verbose_name": "Social provider",
                "verbose_name_plural": "Social providers",
            },
        ),
        migrations.CreateModel(
            name="SSOLoginLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider_slug", models.CharField(db_index=True, max_length=50)),
                ("status", models.CharField(choices=[("success", "Success"), ("failed", "Failed")], db_index=True, max_length=20)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("provider", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="login_logs", to="company_sso_core.socialprovider")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sso_login_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name": "SSO login log",
                "verbose_name_plural": "SSO login logs",
            },
        ),
        migrations.AddIndex(
            model_name="socialprovider",
            index=models.Index(fields=["slug", "workspace_id"], name="company_ss_slug_abc123_idx"),
        ),
        migrations.AddIndex(
            model_name="socialprovider",
            index=models.Index(fields=["is_active"], name="company_ss_is_acti_def456_idx"),
        ),
        migrations.AddIndex(
            model_name="ssologinlog",
            index=models.Index(fields=["provider_slug", "status"], name="company_ss_provide_ghi789_idx"),
        ),
        migrations.AddIndex(
            model_name="ssologinlog",
            index=models.Index(fields=["created_at"], name="company_ss_created_jkl012_idx"),
        ),
    ]
