"""Lookups for the events tagged with a given union.

Design rationale/history: docs/claude_context/event_models.md"""

from django.db import models
from django.utils import timezone

from .pages import EventPage


def _tags_union(event, union):
    """Whether `event`'s own related_unions (regardless of role) tags
    `union` directly -- doesn't roll up sub-events, see
    EventPage.all_related_unions for that. Compares by translation_key so
    an event in one locale still matches a union viewed in another."""
    return any(
        entry.value["union"] is not None
        and entry.value["union"].translation_key == union.translation_key
        for entry in event.related_unions
        if entry.block_type == "union"
    )


def upcoming_events_for_union(union):
    """Live, still-upcoming events tagging `union` in related_unions,
    regardless of role. See docs/claude_context/event_models.md."""
    today = timezone.localdate()
    candidates = (
        EventPage.objects.live()
        .filter(locale=union.locale_id, is_archived=False)
        .filter(
            models.Q(end_date__gte=today)
            | models.Q(end_date__isnull=True, event_date__gte=today)
        )
        .order_by("event_date", "event_time")
    )
    return [event for event in candidates if _tags_union(event, union)]


def events_for_union_between(union, start_date, end_date):
    """Live EventPages tagging `union` (including sub-events -- live()
    isn't tree-depth-filtered, so a union tagged only on one sub-event of a
    bigger event is matched directly here, same as upcoming_events_for_union)
    whose date falls in [start_date, end_date]."""
    candidates = (
        EventPage.objects.live()
        .filter(locale=union.locale_id, is_archived=False)
        .filter(event_date__lte=end_date)
        .filter(
            models.Q(end_date__gte=start_date)
            | models.Q(end_date__isnull=True, event_date__gte=start_date)
        )
        .order_by("event_date", "event_time")
    )
    return [event for event in candidates if _tags_union(event, union)]
