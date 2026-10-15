# pylint: disable=C0114,C0115,C0116
from django.apps import AppConfig
from wagtail.users.apps import WagtailUsersAppConfig


class AccountAppConfig(AppConfig):
    name = "account_app"


class OptionalNamesUsersAppConfig(WagtailUsersAppConfig):
    """Wagtail's users app, with the user forms from wagtail_users.py."""

    user_viewset = "account_app.wagtail_users.UserViewSet"
