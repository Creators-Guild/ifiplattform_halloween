"""App configuration for the ifi_home_app Django application."""

from django.apps import AppConfig


class IfiHomeAppConfig(AppConfig):
    """Configuration class for the ifi_home_app."""

    name = "ifi_home_app"

    def ready(self):
        from .translation import auto_translate, english_overlay, english_urls

        english_overlay.install()
        english_urls.install()
        auto_translate.connect_signals()
