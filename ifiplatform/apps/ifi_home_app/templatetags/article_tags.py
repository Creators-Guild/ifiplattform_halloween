"""Template tags for the menus and the event pages."""

from django import template
from django.utils import timezone

from ifi_home_app.models import menus
from ifi_home_app.models.event.constants import SITE_TIMEZONE
from ifi_home_app.models.event.pages import EventIndexPage
from ifi_home_app.models.event.peoply import PeoplySyncState

register = template.Library()


@register.simple_tag
def get_menu(key):
    """The editor-curated Menu with this key ("sidemenu", "home_dropmenu" or
    "shortcuts"), resolved for the active locale -- see models/menus.py."""
    return menus.get_menu(key)


@register.simple_tag
def get_shortcut_columns():
    """The "shortcuts" Menu's groups, split into their columns in order."""
    columns = {}
    for group in menus.get_menu("shortcuts"):
        columns.setdefault(group["column"], []).append(group)
    return [columns[number] for number in sorted(columns)]


@register.simple_tag
def get_event_index():
    """Return the site's EventIndexPage, used to build links to it (e.g. the
    home events box's "See all events" link, and the event page)."""
    return EventIndexPage.objects.live().first()


@register.simple_tag
def get_peoply_last_synced():
    """When sync_peoply_events last ran successfully, converted to
    SITE_TIMEZONE -- None if it's never run. Stored (and would otherwise
    render) in UTC, this project's settings.TIME_ZONE, not Oslo -- without
    the conversion this is off by the UTC offset (2h in summer/CEST, 1h in
    winter/CET). Site-wide, not per-event: shown on Peoply-sourced event
    pages so visitors know how fresh the data is, since an unchanged event
    gets no new revision on a sync."""
    synced_at = PeoplySyncState.last_synced_at()
    return timezone.localtime(synced_at, timezone=SITE_TIMEZONE) if synced_at else None
