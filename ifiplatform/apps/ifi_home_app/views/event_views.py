"""Views for event-related actions that aren't tied to Wagtail's own page
edit flow (see article_views.py for that side)."""

from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from ifi_home_app.models.event.peoply import PeoplySyncLog


@require_POST
def force_sync_peoply_events(request):
    """Staff-only "Sync Peoply now" button (events/partials/
    peoply_sync_button.html) -- runs sync_peoply_events on demand, for
    catching a new Peoply event without waiting for the next scheduled run
    (deploy/systemd/sync-peoply-events.timer). Redirects back to wherever
    the button was clicked from.

    Every trigger is logged (PeoplySyncLog, superuser-only in Django
    admin) -- the button has no server-side rate limit (just a 5s
    client-side double-click guard), so this is how repeated/spammy use
    would actually be noticed and attributed to whoever did it."""
    if not request.user.is_staff:
        raise PermissionDenied

    PeoplySyncLog.objects.create(user=request.user)
    call_command("sync_peoply_events")
    next_url = request.POST.get("next")
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = "/"
    return redirect(next_url)
