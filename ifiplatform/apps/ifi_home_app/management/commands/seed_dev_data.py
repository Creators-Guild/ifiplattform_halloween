"""Thin entrypoint -- Django's command discovery (find_commands() in
django/core/management/__init__.py) only scans management/commands/ for
plain .py files, explicitly skipping packages (`is_pkg`), so this can't be
a package itself. The actual implementation -- split by content area
(unions/news/events/tools/messages) plus generic helpers -- lives in
ifi_home_app/management/seed_dev_data/ instead; this just re-exports its
Command so `manage.py seed_dev_data` still finds it."""

from ifi_home_app.management.seed_dev_data.command import Command

__all__ = ["Command"]
