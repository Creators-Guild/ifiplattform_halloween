"""Site-wide "a deploy is imminent" banner. See
management/commands/announce_deploy.py (the write side, imports
DEPLOY_NOTICE_CACHE_KEY from here) for how the flag gets set, and
templates/partials/deploy_notice.html (included once in global_base.html) for
how this is actually rendered.

Two read sides:
- deploy_notice(), a context processor giving every page the currently-
  known state at the moment it's rendered (so a page loaded mid-
  announcement shows the banner immediately, no flash-then-appear).
- deploy_notice_status_view(), a small JSON endpoint deploy_notice.js polls
  from *already-open* pages -- the context processor alone only ever runs
  per-request, so it can't make an announcement appear on a tab nobody's
  reloaded or navigated away from; this is what actually does that."""

from django.core.cache import cache
from django.http import JsonResponse

DEPLOY_NOTICE_CACHE_KEY = "deploy_notice_target"


def deploy_notice(request):
    """Context processor -- adds deploy_notice_target (epoch seconds, or
    None if no deploy is currently announced/the announcement has expired)
    to every template's context. cache.get() already returns None past its
    own timeout, so an elapsed announcement needs no special-casing here."""
    return {"deploy_notice_target": cache.get(DEPLOY_NOTICE_CACHE_KEY)}


def deploy_notice_status_view(request):
    """Polled by deploy_notice.js every POLL_INTERVAL_SECONDS from every
    page, active announcement or not -- lets an already-open tab pick up a
    new announcement (or notice one just got cleared) without the visitor
    having to reload or navigate anywhere themselves."""
    return JsonResponse({"target": cache.get(DEPLOY_NOTICE_CACHE_KEY)})
