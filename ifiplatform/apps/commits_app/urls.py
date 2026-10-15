"""URL configuration for commits app."""

from django.conf import settings
from django.urls import path
from django.utils.translation import gettext_lazy as _
from core_app.under_development import under_development_urlpatterns
from .views import core_views

if settings.APPS_UNDER_DEVELOPMENT.get("commits_app"):
    urlpatterns = under_development_urlpatterns("commits_main", _("Commits"))
else:
    urlpatterns = [
        path("", core_views.main_view, name="commits_main"),
        path("leaderboard/", core_views.leaderboard_view, name="commits_leaderboard"),
        path(
            "leaderboard/drink/<int:user_id>/",
            core_views.hand_out_drink_view,
            name="commits_hand_out_drink",
        ),
        path("leaderboard/sync/", core_views.sync_now_view, name="commits_sync_now"),
        path("issues/", core_views.issues_view, name="commits_issues"),
        path(
            "issues/<int:number>/",
            core_views.issue_detail_view,
            name="commits_issue_detail",
        ),
        path("issues/lucky/", core_views.lucky_view, name="commits_lucky"),
        path(
            "issues/<int:number>/claim/", core_views.claim_view, name="commits_claim"
        ),
        path(
            "issues/<int:number>/release/",
            core_views.release_view,
            name="commits_release",
        ),
        path("issues/<int:number>/keep/", core_views.keep_view, name="commits_keep"),
        path(
            "issues/<int:number>/time/",
            core_views.claim_time_view,
            name="commits_claim_time",
        ),
    ]
