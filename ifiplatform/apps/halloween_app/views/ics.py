"""Add an event to your calendar: an .ics file for one event page. Not built
yet: that's an event issue."""

from django.http import Http404


def event_ics_view(request, page_id):
    raise Http404("Not built yet")
