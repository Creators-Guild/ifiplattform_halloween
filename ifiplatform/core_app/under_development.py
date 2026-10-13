"""Reusable placeholder for apps/sections that aren't built yet.

Controlled via the ``APPS_UNDER_DEVELOPMENT`` setting: an app's urls.py can
check its own flag and, if enabled, replace its real urlpatterns with
``under_development_urlpatterns(name, app_name)`` so every route under that
app shows this placeholder instead.
"""

from django.shortcuts import render
from django.urls import re_path


def under_development_view(request, app_name):
    """Render a simple placeholder for a section that isn't built yet."""
    return render(request, "under_development.html", {"app_name": app_name})


def under_development_urlpatterns(url_name, app_name):
    """A catch-all urlpatterns list showing the placeholder for any path under
    it, keeping ``url_name`` resolvable so {% url %} references elsewhere
    (e.g. in the navbar) still work. ``app_name`` is the human-readable label
    shown on the placeholder page (e.g. "Study")."""
    return [
        re_path(
            r"^.*$",
            under_development_view,
            kwargs={"app_name": app_name},
            name=url_name,
        )
    ]
