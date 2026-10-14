"""Thin entrypoint, like seed_dev_data.py next to it: Django only finds
plain .py files in management/commands/. The implementation lives in
ifi_home_app/management/seed_halloween_data/."""

from ifi_home_app.management.seed_halloween_data.command import Command

__all__ = ["Command"]
