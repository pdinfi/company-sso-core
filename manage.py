#!/usr/bin/env python
"""Django manage.py for running tests and migrations from package root."""
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Django must be installed.") from exc
    execute_from_command_line(sys.argv)
