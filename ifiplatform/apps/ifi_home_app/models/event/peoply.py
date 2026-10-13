"""Models recording the state of the Peoply sync: when it last ran,
who triggered it by hand, union<->organization mismatches, and events
Peoply has dropped. The sync itself lives in
management/commands/sync_peoply_events.py.

Design rationale/history: docs/claude_context/event_models.md"""

from django.conf import settings
from django.db import models


class PeoplySyncState(models.Model):
    """Singleton row (always pk=1) -- see touch()/last_synced_at(). Mirrors
    GlossarySyncState's own pattern (glossary_models.py)."""

    synced_at = models.DateTimeField(auto_now=True)

    @classmethod
    def touch(cls):
        """Call after a successful sync_peoply_events run."""
        obj, _created = cls.objects.get_or_create(pk=1)
        obj.save()  # bumps synced_at via auto_now even if just created
        return obj.synced_at

    @classmethod
    def last_synced_at(cls):
        """None if sync_peoply_events has never run successfully."""
        obj = cls.objects.filter(pk=1).first()
        return obj.synced_at if obj else None


class PeoplySyncLog(models.Model):
    """One row per click of the "Sync Peoply now" button (events/partials/
    peoply_sync_button.html, event_views.force_sync_peoply_events) -- who
    triggered a manual sync and when, so repeated/spammy use is
    attributable to a specific person. Superuser-only in Django admin, see
    PeoplySyncLogAdmin (admin.py); nothing here creates or edits rows by
    hand."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    triggered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-triggered_at"]

    def __str__(self):
        return f"{self.user} at {self.triggered_at}"


class PeoplyUnionMismatch(models.Model):
    """One durable row per UnionPage<->Peoply-organization mismatch the
    check_peoply_union_matches command has ever found -- so a discovery
    survives past whatever single terminal/journalctl output printed it,
    and repeated scheduled runs (see sync_peoply_events, which runs that
    command automatically every 6 hours) don't have to re-announce the same
    already-known gap forever.

    (kind, identifier) is the stable identity of one mismatch: identifier
    is the union's translation_key for "unlinked_union"/"stale_link"/
    "pending_link" (nb/en both share it, and it survives a slug/title
    change), or Peoply's own organization id for "missing_org".
    first_seen_at is set once; last_seen_at is bumped every run the
    mismatch is still present; resolved_at is set the first run it's no
    longer found (e.g. someone linked/created the union, or Peoply's data
    changed) and cleared again if it ever comes back, rather than creating
    a second row for the same (kind, identifier)."""

    KIND_CHOICES = [
        ("unlinked_union", "Site union has no matching Peoply organization"),
        (
            "stale_link",
            "Site union's peoply_organization_id no longer matches any Peoply organization",
        ),
        ("missing_org", "Peoply organization has no matching UnionPage here"),
        ("pending_link", "Site union has an exact Peoply match, not linked yet"),
    ]
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    identifier = models.CharField(
        max_length=64,
        help_text="UnionPage.translation_key for unlinked_union/stale_link/pending_link, Peoply organization id for missing_org.",
    )
    label = models.CharField(
        max_length=255,
        help_text="Human-readable description, refreshed on every sighting.",
    )
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "identifier"], name="unique_peoply_union_mismatch"
            ),
        ]
        ordering = ["-last_seen_at"]

    def __str__(self):
        return f"{self.get_kind_display()}: {self.label}"


class _SingleKindMismatchManager(models.Manager):
    """Backs each PeoplyUnionMismatch proxy below -- restricts the default
    manager to just that proxy's own kind, so e.g. PeoplyOrgsWithoutUnion's
    admin changelist (get_queryset() included) only ever shows "missing_org"
    rows, never the other two kinds sharing the same underlying table."""

    def __init__(self, kind):
        super().__init__()
        self._kind = kind

    def get_queryset(self):
        return super().get_queryset().filter(kind=self._kind)


class UnionsWithoutPeoplyOrg(PeoplyUnionMismatch):
    """Proxy over PeoplyUnionMismatch, scoped to kind="unlinked_union" --
    site UnionPages with no peoply_organization_id and no exact Peoply
    name/urlId match either. A separate admin entry from
    PeoplyOrgsWithoutUnion (the reverse direction) and
    UnionsWithStalePeoplyLink (a union that *did* have a link, now broken)
    rather than one combined filterable list, since the three read as
    distinct problems needing distinct fixes -- see
    check_peoply_union_matches's own docstring."""

    objects = _SingleKindMismatchManager("unlinked_union")

    class Meta:
        proxy = True
        verbose_name = "site union without a Peoply organization"
        verbose_name_plural = "Site unions without a Peoply organization"


class UnionsWithStalePeoplyLink(PeoplyUnionMismatch):
    """Proxy over PeoplyUnionMismatch, scoped to kind="stale_link" -- site
    UnionPages whose peoply_organization_id no longer matches any
    organization Peoply currently returns. See UnionsWithoutPeoplyOrg's own
    docstring on why this is a separate admin entry rather than folded into
    that one, even though both describe "this union has no working Peoply
    match right now": this one had a real link that broke, which usually
    means "fix the id" rather than "find/create the union on Peoply"."""

    objects = _SingleKindMismatchManager("stale_link")

    class Meta:
        proxy = True
        verbose_name = "site union with a stale Peoply link"
        verbose_name_plural = "Site unions with a stale Peoply link"


class PeoplyOrgsWithoutUnion(PeoplyUnionMismatch):
    """Proxy over PeoplyUnionMismatch, scoped to kind="missing_org" --
    Peoply organizations with no matching UnionPage here at all. Creating a
    stub only makes sense in this direction (create_union_pages_for_missing_orgs,
    admin.py)."""

    objects = _SingleKindMismatchManager("missing_org")

    class Meta:
        proxy = True
        verbose_name = "Peoply organization without a site union"
        verbose_name_plural = "Peoply organizations without a site union"


class UnionsPendingPeoplyLink(PeoplyUnionMismatch):
    """Proxy over PeoplyUnionMismatch, scoped to kind="pending_link" --
    site UnionPages with no peoply_organization_id set, but whose title is
    an exact match (case-insensitive, name or urlId) against a Peoply
    organization -- check_peoply_union_matches finds these via the same
    find_exact_match link_peoply_organizations uses, but doesn't write
    anything itself (read-only command). A separate kind from
    "unlinked_union" specifically because the fix here is just linking, not
    finding/creating the union on Peoply -- link_selected_unions
    (admin.py) does exactly that in one click."""

    objects = _SingleKindMismatchManager("pending_link")

    class Meta:
        proxy = True
        verbose_name = "site union with an unlinked Peoply match"
        verbose_name_plural = "Site unions with an unlinked Peoply match"


class PeoplyRemovedEvent(models.Model):
    """One durable row per Peoply-sourced EventPage that sync_peoply_events
    found missing from Peoply's own /events response (deleted or cancelled
    there) -- the sync unpublishes the page itself, this row is what lets
    a superuser then decide in Django admin (PeoplyRemovedEventAdmin,
    admin.py) whether to delete it for good or archive it under "previous
    events". Keyed by external_uid, same reopen-rather-than-duplicate
    convention as PeoplyUnionMismatch: resolved_at/resolution are set once
    the event reappears on Peoply or an admin acts on it, and cleared again
    if it goes missing a second time."""

    RESOLUTION_CHOICES = [
        ("", "Open"),
        ("reappeared", "Reappeared on Peoply"),
        ("archived", "Archived under previous events"),
        ("deleted", "Deleted"),
    ]
    external_uid = models.CharField(max_length=200, unique=True)
    title = models.CharField(max_length=255)
    event_date = models.DateField()
    page = models.ForeignKey(
        "EventPage", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution = models.CharField(max_length=20, choices=RESOLUTION_CHOICES, blank=True)

    class Meta:
        ordering = ["-last_seen_at"]
        verbose_name = "event removed from Peoply"
        verbose_name_plural = "Events removed from Peoply"

    def __str__(self):
        return f"{self.title} ({self.event_date})"


# Fields sync_peoply_events overwrites from Peoply on every run -- read-only
# in wagtail-admin for peoply-sourced events (EventPageForm below), since
# any edit here would just be reverted by the next sync.
PEOPLY_SYNCED_FIELDS = [
    "title",
    "event_date",
    "event_time",
    "event_end_time",
    "end_date",
    "location",
    "intro",
    "peoply_url",
    "signup_url",
]
