"""URL configuration for yourpage app."""

from django.conf import settings
from django.urls import path
from django.utils.translation import gettext_lazy as _
from core_app.under_development import under_development_urlpatterns
from .views import core_views

if settings.APPS_UNDER_DEVELOPMENT.get("yourpage_app"):
    urlpatterns = under_development_urlpatterns("yourpage_main", _("Commits"))
else:
    urlpatterns = [
        path("", core_views.main_view, name="yourpage_main"),
        path("leaderboard/", core_views.leaderboard_view, name="yourpage_leaderboard"),
        path(
            "leaderboard/drink/<int:user_id>/",
            core_views.hand_out_drink_view,
            name="yourpage_hand_out_drink",
        ),
        path("leaderboard/sync/", core_views.sync_now_view, name="yourpage_sync_now"),
        path("issues/", core_views.issues_view, name="yourpage_issues"),
        path(
            "issues/<int:number>/",
            core_views.issue_detail_view,
            name="yourpage_issue_detail",
        ),
    ]
