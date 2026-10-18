# pylint: disable=C0114,C0115,C0116
from django.apps import AppConfig


class HalloweenAppConfig(AppConfig):
    """The Halloween corner (/halloween/) for Commit for Candy: small pages that
    the event issues fill in. No models."""

    name = "halloween_app"
    verbose_name = "Halloween corner"
