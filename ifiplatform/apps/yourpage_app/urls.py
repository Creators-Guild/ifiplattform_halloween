"""URL configuration for yourpage app."""

from django.conf import settings
from django.urls import path
from django.utils.translation import gettext_lazy as _
from core_app.under_development import under_development_urlpatterns
from .views import core_views

if settings.APPS_UNDER_DEVELOPMENT.get("yourpage_app"):
    urlpatterns = under_development_urlpatterns("yourpage_main", _("Your Page"))
else:
    urlpatterns = [path("", core_views.main_view, name="yourpage_main")]
