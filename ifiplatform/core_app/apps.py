"""App configuration for the core_app Django application."""

from django.apps import AppConfig
from django.contrib.staticfiles.apps import StaticFilesConfig


class CoreAppConfig(AppConfig):
    """Configuration class for core_app."""

    name = "core_app"


class DocsExcludedStaticFilesConfig(StaticFilesConfig):
    """staticfiles, but collectstatic skips README.md.

    Each static/css/ folder keeps a README next to the CSS it documents, which
    is the point -- but collectstatic copies every file in a static dir
    regardless of extension, so those READMEs were being served publicly at
    /static/css/README.md. They belong in the repo, not on the site.

    Replaces "django.contrib.staticfiles" in INSTALLED_APPS. Only affects
    collectstatic: with DEBUG=True, runserver serves via the finders, which
    do not consult ignore_patterns, so the file is still reachable locally.
    """

    ignore_patterns = StaticFilesConfig.ignore_patterns + ["README.md"]
