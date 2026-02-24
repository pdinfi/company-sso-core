"""Django signals for SSO events."""
from django.dispatch import Signal

# Sent after a successful SSO login (user and log created).
sso_login_success = Signal()

# Sent after a failed SSO login attempt (log created).
sso_login_failed = Signal()
