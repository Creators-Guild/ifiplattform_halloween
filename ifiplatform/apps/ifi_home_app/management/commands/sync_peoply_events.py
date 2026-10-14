"""Mirrors Peoply's events into EventPages, one run per UnionPage that has a
peoply_organization_id set (see that field's own help text).

Peoply is the source of truth for PEOPLY_SYNCED_FIELDS (models/event/peoply.py):
an event already synced (matched by external_source="peoply" +
external_uid) gets those fields overwritten on every run if they changed on
Peoply -- and they're read-only in wagtail-admin (EventPageForm) so nobody's
edit gets silently reverted. Everything else (event_type, colors, tags, map
links, related_unions, ...) is only set on create and left to editors after.
Unchanged events get no new revision.

An event that was synced before but is no longer returned by Peoply (within
the same after_date window this run asked for, for a union synced this
run) is unpublished and logged as a PeoplyRemovedEvent, for a superuser to
delete or archive from Django admin. If it later reappears on Peoply, it's
republished and that log row marked resolved.

After syncing, clears Wagtail's site-root-paths cache (bulk page-tree
churn like this doesn't trigger Wagtail's own cache invalidation, which only
listens for Site row changes -- confirmed the hard way once, see
clear_cache's own docstring). That makes every caller -- the scheduled
systemd timer, a local dev running this by hand, and the "Sync Peoply now"
admin button -- self-contained, with nothing extra to run afterwards."""

from datetime import datetime, time, timedelta, timezone as dt_timezone
from html import escape

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.text import slugify

from wagtail.coreutils import find_available_slug
from wagtail.models import Locale, Site

from ifi_home_app.integrations.peoply_api import get_events
from ifi_home_app.models.article.unions import UnionPage
from ifi_home_app.models.event.constants import SITE_TIMEZONE
from ifi_home_app.models.event.pages import EventIndexPage, EventPage
from ifi_home_app.models.event.peoply import (
    PEOPLY_SYNCED_FIELDS,
    PeoplyRemovedEvent,
    PeoplySyncState,
)


def _plain_text_to_html(text):
    """Peoply's description is plain text with \\r\\n line breaks, not HTML
    -- RichTextField expects HTML. A blank line becomes a paragraph break, a
    single line break becomes <br/>."""
    paragraphs = text.replace("\r\n", "\n").split("\n\n")
    return "".join(
        f"<p>{escape(paragraph).replace(chr(10), '<br/>')}</p>"
        for paragraph in paragraphs
        if paragraph.strip()
    )


def _to_local(iso_string):
    """Peoply timestamps are ISO-8601 UTC -- convert to the site's own
    timezone so event_date/event_time land on the right local day/hour."""
    parsed = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    return parsed.astimezone(SITE_TIMEZONE)


def _infer_event_type(title):
    """Peoply events are overwhelmingly social (pub crawls, parties,
    workshops, ...), but "Bedriftspresentasjon" ("company presentation") in
    the title is a reliable enough signal to tag those as EventPage's
    "company" type instead -- common for unions like Navet that host a lot
    of them. Only applied on create -- editors can correct it by hand after
    and the sync won't undo that."""
    if "bedriftspresentasjon" in title.lower():
        return "company"
    return "social"


def _peoply_fields(event):
    """PEOPLY_SYNCED_FIELDS for one Peoply event, as EventPage field values.
    event_end_time and end_date are always both present (one of them None)
    so an update from one end-mode to the other clears the stale one."""
    start = _to_local(event["startDate"])
    end = _to_local(event["endDate"]) if event.get("endDate") else None

    fields = {
        "title": event["title"],
        "event_date": start.date(),
        "event_time": start.time(),
        "event_end_time": None,
        "end_date": None,
        "location": (event.get("freeformAddress") or event.get("locationName") or "")[
            :200
        ],
        "intro": _plain_text_to_html(event.get("description") or ""),
        "peoply_url": f"https://peoply.app/events/{event['urlId']}",
        # Only ever set when Peoply's own registrationMode is "EXTERNAL" --
        # confirmed empirically (99 real events sampled) that "PEOPLY"-mode
        # events always have a null externalUrl, and every "EXTERNAL"-mode
        # one has a real one. Left blank for "PEOPLY" mode -- event_page.html
        # uses that (blank signup_url on a peoply-sourced event) to tell
        # "sign up on Peoply itself" apart from "sign up somewhere else",
        # rather than needing a separate field.
        "signup_url": event.get("externalUrl") or "",
    }
    if end is not None:
        # end_date means "still happening" for every hour of that whole day
        # too (EventPage.is_happening_now checks calendar dates, not clock
        # time) -- correct for a genuine multi-day event, but wrong for a
        # normal party that just runs past local midnight: Peoply's own UTC
        # timestamps are same-day (e.g. 16:00-23:00 UTC), and only *look*
        # cross-day after converting to Oslo time (CEST is UTC+2, so 23:00
        # UTC becomes 01:00 the next local day). Confirmed against real
        # synced data -- a CYB event stored this way showed as "happening
        # now" for nearly 24h after it had actually ended. A same-day end
        # before this cutoff is assumed to be that kind of overflow, not a
        # real multi-day event; treated as ending within the start day for
        # is_happening_now's purposes, even though the clock time is
        # technically past midnight.
        next_day_early_morning = end.date() == start.date() + timedelta(
            days=1
        ) and end.time() < time(6, 0)
        if end.date() == start.date() or next_day_early_morning:
            fields["event_end_time"] = end.time()
        else:
            fields["end_date"] = end.date()
    return fields


def _host_union_id(page):
    for entry in page.related_unions:
        if (
            entry.block_type == "union"
            and entry.value["role"] == "host"
            and entry.value["union"]
        ):
            return entry.value["union"].pk
    return None


def _starts_on_or_after(page, after_date):
    start = datetime.combine(
        page.event_date, page.event_time or time.min, tzinfo=SITE_TIMEZONE
    )
    return start >= after_date


class Command(BaseCommand):
    help = (
        "Syncs EventPages from Peoply for every UnionPage with a "
        "peoply_organization_id set: creates new events, updates changed "
        "ones, and hides (and logs) events no longer on Peoply."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--after",
            help="YYYY-MM-DD -- only sync events starting on/after this date. Defaults to now.",
        )

    def handle(self, *args, **options):
        after_date = (
            datetime.strptime(options["after"], "%Y-%m-%d").replace(
                tzinfo=dt_timezone.utc
            )
            if options["after"]
            else timezone.now()
        )

        try:
            nb_locale = Locale.objects.get(language_code="nb")
        except Locale.DoesNotExist as exc:
            raise CommandError("No nb Locale found -- run migrate first.") from exc

        event_index = EventIndexPage.objects.live().filter(locale=nb_locale).first()
        if event_index is None:
            raise CommandError(
                "No live nb EventIndexPage found to create synced events under."
            )

        unions = UnionPage.objects.live().exclude(peoply_organization_id="")
        synced_union_ids = set()
        # Fetch every union first -- get_events raises on an outage, and
        # removal detection below must never run on a partial fetch.
        fetched = []
        for union in unions:
            synced_union_ids.add(union.pk)
            fetched += [
                (union, event)
                for event in get_events(union.peoply_organization_id, after_date)
            ]

        counts = {
            "created": 0,
            "updated": 0,
            "unchanged": 0,
            "restored": 0,
            "hidden": 0,
        }
        fetched_uids = set()

        for union, event in fetched:
            fetched_uids.add(event["id"])
            fields = _peoply_fields(event)
            page = EventPage.objects.filter(
                external_source="peoply", external_uid=event["id"], locale=nb_locale
            ).first()
            removal = PeoplyRemovedEvent.objects.filter(
                external_uid=event["id"], resolved_at__isnull=True
            ).first()
            if removal is not None:
                removal.resolved_at = timezone.now()
                removal.resolution = "reappeared"
                removal.save()

            if page is None:
                page = EventPage(
                    **fields,
                    slug=find_available_slug(event_index, slugify(event["title"])),
                    locale=nb_locale,
                    event_type=_infer_event_type(event["title"]),
                    external_source="peoply",
                    external_uid=event["id"],
                    related_unions=[("union", {"union": union, "role": "host"})],
                )
                event_index.add_child(instance=page)
                page.save_revision().publish()
                counts["created"] += 1
                self.stdout.write(f"  created EventPage: {event['title']}")
                continue

            restoring = removal is not None or page.is_archived
            if not page.live and not restoring:
                # Unpublished by an editor, not by this sync -- leave it
                # hidden. It gets caught up the next run after republishing.
                counts["unchanged"] += 1
                continue

            changed = any(
                getattr(page, name) != fields[name] for name in PEOPLY_SYNCED_FIELDS
            )
            if changed or restoring:
                for name, value in fields.items():
                    setattr(page, name, value)
                page.is_archived = False
                page.save_revision().publish()
                if restoring:
                    counts["restored"] += 1
                    self.stdout.write(
                        f"  restored EventPage (back on Peoply): {event['title']}"
                    )
                else:
                    counts["updated"] += 1
                    self.stdout.write(f"  updated EventPage: {event['title']}")
            else:
                counts["unchanged"] += 1

        candidates = (
            EventPage.objects.live()
            .filter(external_source="peoply", locale=nb_locale, is_archived=False)
            .exclude(external_uid__in=fetched_uids)
        )
        for page in candidates:
            if not _starts_on_or_after(page, after_date):
                continue
            if _host_union_id(page) not in synced_union_ids:
                continue

            page.unpublish()
            PeoplyRemovedEvent.objects.update_or_create(
                external_uid=page.external_uid,
                defaults={
                    "title": page.title,
                    "event_date": page.event_date,
                    "page": page,
                    "resolved_at": None,
                    "resolution": "",
                },
            )
            counts["hidden"] += 1
            self.stdout.write(f"  hid EventPage (gone from Peoply): {page.title}")

        Site.clear_site_root_paths_cache()

        PeoplySyncState.touch()
        self.stdout.write(
            self.style.SUCCESS(
                "Done: {created} created, {updated} updated, {unchanged} unchanged, "
                "{restored} restored, {hidden} hidden (gone from Peoply).".format(
                    **counts
                )
            )
        )

        # Read-only (never passes --create-missing here) -- just so the
        # union/organization mismatch warnings reach the same
        # terminal/journalctl output this command's own systemd timer
        # already produces every 6 hours, without a second schedule. A
        # failure here (e.g. Peoply's own API being down) shouldn't undo
        # the event sync that already succeeded above, so it's reported
        # rather than left to blow up the whole run.
        try:
            call_command("check_peoply_union_matches")
        except CommandError as exc:
            self.stderr.write(f"check_peoply_union_matches failed: {exc}")
