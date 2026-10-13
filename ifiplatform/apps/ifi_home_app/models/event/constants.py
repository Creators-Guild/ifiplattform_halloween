"""Constants shared across the Events section.

Design rationale/history: docs/claude_context/event_models.md"""

from zoneinfo import ZoneInfo

from django.utils.translation import gettext_lazy as _

# settings.TIME_ZONE is UTC; used where Oslo clock time matters (turning
# Peoply's UTC times into event_time, and showing the last sync time) --
# see docs/claude_context/event_models.md.
SITE_TIMEZONE = ZoneInfo("Europe/Oslo")

EVENT_CALENDAR_COLOR_CHOICES = [
    ("", _("Auto (by event type)")),
    ("blue", _("Blue")),
    ("yellow", _("Yellow")),
    ("orange", _("Orange")),
    ("pink", _("Pink")),
    ("green", _("Green")),
    ("purple", _("Purple")),
    ("custom", _("Custom (hex code)")),
]


EVENT_TYPE_CHOICES = [
    ("social", _("Social")),
    ("deadline", _("Deadline")),
    ("academic", _("Academic")),
    ("company", _("Company presentation")),
    ("other", _("Other")),
]


# Roles a union can have on an event. Single source for both the
# ChoiceBlock in blocks.py and EventPage.all_related_unions' role_label,
# so the words aren't defined twice.
UNION_ROLE_CHOICES = [
    ("host", _("Host")),
    ("contributor", _("Contributor")),
    ("collaborator", _("Collaborator")),
]
