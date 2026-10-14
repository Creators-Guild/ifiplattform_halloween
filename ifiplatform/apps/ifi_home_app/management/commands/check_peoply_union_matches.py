"""Cross-checks IFI's UnionPages against Peoply's full organization roster,
in both directions -- unlike link_peoply_organizations (which only ever
looks at site unions missing a peoply_organization_id, one at a time via
Peoply's name search), this fetches every organization Peoply knows about
and reports:

Only considers status="active" unions -- retired/unknown ones aren't
expected to have a working Peoply link, so they never get flagged.

- site unions with no corresponding Peoply organization at all (no id set,
  and no exact name/urlId match either) -- these can't get automatic event
  sync (see UnionPage.peoply_organization_id's own help text) until someone
  either finds/creates the union on Peoply, or accepts it just isn't there.
- site unions whose peoply_organization_id no longer matches any org Peoply
  currently returns (a stale link -- e.g. the union's Peoply id changed, or
  the org was removed there). sync_peoply_events would silently do nothing
  for these (Peoply's /events endpoint just returns no rows for an unknown
  organizationId rather than erroring), so this is the only thing that
  would ever surface it.
- Peoply organizations with no matching UnionPage here at all. Pass
  --create-missing to create a draft (unpublished) UnionPage stub for each,
  pre-filled with its Peoply id and website -- left for an editor to
  review, fill in, and publish by hand rather than going live unattended.
- site unions with no peoply_organization_id set, but whose title is an
  exact match against a Peoply organization -- these aren't counted as
  "missing" on either side, just not linked here yet. Surfaced as their own
  kind (not silently absorbed) so there's a log to act on -- see
  UnionsPendingPeoplyLink's "link selected" admin action, or run
  link_peoply_organizations --apply.

Every mismatch found is also reconciled against PeoplyUnionMismatch (see
that model's own docstring, models/event/peoply.py) -- a mismatch seen for the
first time is a NEW row and gets called out separately from ones already
known about, and a previously-flagged mismatch that no longer shows up gets
marked resolved automatically. Without this, the scheduled run below would
re-announce the exact same already-known gaps every 6 hours forever, with
no way to tell "still broken" from "just noticed".

Read-only and safe to run anytime, including unattended -- only
--create-missing writes a UnionPage; the mismatch bookkeeping above always
happens regardless. sync_peoply_events runs this automatically at the end
of every sync, so these warnings reach the same terminal/journalctl output
its systemd timer already produces every 6 hours, without needing a second
schedule of its own (see that command)."""

import requests
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.text import slugify

from wagtail.coreutils import find_available_slug
from wagtail.models import Locale

from ifi_home_app.integrations.peoply_api import find_exact_match, get_organizations
from ifi_home_app.models.article.unions import StudentUnionCategoryPage, UnionPage
from ifi_home_app.models.event.peoply import PeoplyUnionMismatch


class Command(BaseCommand):
    help = (
        "Cross-checks UnionPages against Peoply's full organization list: "
        "site unions with no Peoply match, unions whose "
        "peoply_organization_id is stale, and Peoply organizations with no "
        "UnionPage here (pass --create-missing to create draft stubs for "
        "those). Every finding is persisted to PeoplyUnionMismatch, so "
        "repeated runs only call out what's newly discovered or resolved."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--create-missing",
            action="store_true",
            help="Create a draft (unpublished) UnionPage stub for every Peoply organization with no matching union here. Without this, they're only reported.",
        )
        parser.add_argument(
            "--parent-slug",
            help="Slug of the StudentUnionCategoryPage to create stubs under, only needed with --create-missing when more than one exists in the nb locale.",
        )

    def handle(self, *args, **options):
        try:
            nb_locale = Locale.objects.get(language_code="nb")
        except Locale.DoesNotExist as exc:
            raise CommandError("No nb Locale found -- run migrate first.") from exc

        try:
            orgs = get_organizations()
        except requests.RequestException as exc:
            raise CommandError(f"Couldn't fetch Peoply's organizations: {exc}") from exc

        orgs_by_id = {org["id"]: org for org in orgs}
        # status="active" only -- retired/unknown unions aren't expected to
        # have a working Peoply link, so they're excluded from every check
        # below, not just reported differently. A union that later gets
        # retired/marked unknown drops out of `current` on its own, so any
        # mismatch already on file for it gets auto-resolved next run (see
        # _reconcile_mismatches) without needing special-casing here.
        unions = list(
            UnionPage.objects.live()
            .filter(locale=nb_locale, status="active")
            .order_by("title")
        )

        unlinked = []  # no peoply_organization_id, and no exact name/urlId match either
        stale = []  # peoply_organization_id no longer matches any org Peoply returns
        pending_link = (
            []
        )  # (union, org) -- no peoply_organization_id, but an exact match exists
        matched_org_ids = set()

        for union in unions:
            if union.peoply_organization_id:
                if union.peoply_organization_id in orgs_by_id:
                    matched_org_ids.add(union.peoply_organization_id)
                else:
                    stale.append(union)
                continue

            org = find_exact_match(union.title, orgs)
            if org:
                # Accounted for on Peoply, just not linked here yet -- not a
                # missing-organization problem, so it's excluded from
                # missing_here below. Still surfaced of its own accord (not
                # silently dropped) so there's a log to link it from, via
                # UnionsPendingPeoplyLink's "link selected" admin action or
                # link_peoply_organizations --apply.
                matched_org_ids.add(org["id"])
                pending_link.append((union, org))
            else:
                unlinked.append(union)

        missing_here = [org for org in orgs if org["id"] not in matched_org_ids]

        # (identifier, label) pairs per kind -- identifier is the stable
        # PeoplyUnionMismatch key, label is what gets printed/stored.
        unlinked_items = [
            (str(union.translation_key), union.title) for union in unlinked
        ]
        stale_items = [
            (
                str(union.translation_key),
                f"{union.title} ({union.peoply_organization_id})",
            )
            for union in stale
        ]
        pending_link_items = [
            (
                str(union.translation_key),
                f"{union.title} -> {org['name']} ({org['urlId'] or org['id']})",
            )
            for union, org in pending_link
        ]
        missing_items = [
            (org["id"], f"{org['name']} ({org['urlId']})") for org in missing_here
        ]

        current = (
            [("unlinked_union", *item) for item in unlinked_items]
            + [("stale_link", *item) for item in stale_items]
            + [("missing_org", *item) for item in missing_items]
            + [("pending_link", *item) for item in pending_link_items]
        )
        new_records, resolved_records = self._reconcile_mismatches(current)

        if not current:
            self.stdout.write(
                self.style.SUCCESS("Every union and Peoply organization matches up.")
            )
        else:
            new_keys = {(record.kind, record.identifier) for record in new_records}
            self._report(
                "unlinked_union",
                unlinked_items,
                "union(s) on this site have no matching Peoply organization",
                new_keys,
            )
            self._report(
                "stale_link",
                stale_items,
                "union(s) have a peoply_organization_id Peoply no longer recognizes -- check/re-link by hand",
                new_keys,
            )
            self._report(
                "missing_org",
                missing_items,
                "Peoply organization(s) have no matching union on this site",
                new_keys,
            )
            self._report(
                "pending_link",
                pending_link_items,
                "union(s) have an exact Peoply match but aren't linked yet -- see admin action to link them",
                new_keys,
            )

        if resolved_records:
            self.stdout.write(
                self.style.SUCCESS(
                    f"{len(resolved_records)} previously-flagged mismatch(es) no longer apply, marked resolved: "
                    + ", ".join(record.label for record in resolved_records)
                )
            )

        if not missing_here:
            return
        if not options["create_missing"]:
            self.stdout.write(
                "Pass --create-missing to create a draft UnionPage stub for each of those."
            )
            return

        parent = self._resolve_parent(nb_locale, options["parent_slug"])
        created = 0
        for org in missing_here:
            page = UnionPage(
                title=org["name"],
                slug=find_available_slug(parent, slugify(org["name"])),
                locale=nb_locale,
                peoply_organization_id=org["id"],
                website_url=org.get("websiteUrl") or "",
                status="unknown",
                live=False,  # draft only -- add_child() alone would leave it
                # live (Page.live defaults True); needs review first
            )
            parent.add_child(instance=page)
            page.save_revision()
            created += 1
            self.stdout.write(f"  created draft UnionPage: {org['name']}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created} draft stub(s) -- review, fill in, and publish each by hand in wagtail-admin."
            )
        )

    def _report(self, kind, items, message, new_keys):
        """Prints a WARNING for (identifier, label) `items` of the given
        kind, splitting out which ones are brand new this run (just written
        to PeoplyUnionMismatch for the first time) from ones already known
        about, so a scheduled run doesn't read as "everything is broken"
        when really nothing has changed since last time."""
        if not items:
            return

        new_labels = [
            label for identifier, label in items if (kind, identifier) in new_keys
        ]
        known_labels = [
            label for identifier, label in items if (kind, identifier) not in new_keys
        ]

        if new_labels:
            self.stdout.write(
                self.style.ERROR(
                    f"NEW: {len(new_labels)} {message}: " + ", ".join(new_labels)
                )
            )
        if known_labels:
            self.stdout.write(
                self.style.WARNING(
                    f"(already known) {len(known_labels)} {message}: "
                    + ", ".join(known_labels)
                )
            )

    def _reconcile_mismatches(self, current):
        """current is a list of (kind, identifier, label) tuples found this
        run. (kind, identifier) is unique-constrained on PeoplyUnionMismatch
        (including already-resolved rows), so every existing row -- not
        just open ones -- has to be checked before creating a new one, or a
        mismatch that resolved and later reappears would collide with its
        own old row instead of reopening it.

        Creates a row for any (kind, identifier) never seen before, reopens
        (clears resolved_at on) any resolved row that's reappeared, and
        refreshes label/last_seen_at on ones still open. Any open row not
        in `current` gets marked resolved. Returns (newly_created_or_
        reopened, newly_resolved) -- both reported as PeoplyUnionMismatch
        instances."""
        current_keys = {(kind, identifier) for kind, identifier, _label in current}
        all_records = {
            (record.kind, record.identifier): record
            for record in PeoplyUnionMismatch.objects.all()
        }

        new_records = []
        for kind, identifier, label in current:
            existing = all_records.get((kind, identifier))
            if existing is None:
                new_records.append(
                    PeoplyUnionMismatch.objects.create(
                        kind=kind, identifier=identifier, label=label
                    )
                )
            elif existing.resolved_at is not None:
                existing.label = label
                existing.resolved_at = None
                existing.save()
                new_records.append(existing)
            else:
                # Always saved, not just on a label change -- last_seen_at
                # (auto_now) needs bumping on every run this is still
                # present, not only when its label happens to differ.
                existing.label = label
                existing.save()

        resolved_records = []
        for key, record in all_records.items():
            if key not in current_keys and record.resolved_at is None:
                record.resolved_at = timezone.now()
                record.save()
                resolved_records.append(record)

        return new_records, resolved_records

    def _resolve_parent(self, nb_locale, parent_slug):
        categories = StudentUnionCategoryPage.objects.live().filter(locale=nb_locale)
        if parent_slug:
            parent = categories.filter(slug=parent_slug).first()
            if parent is None:
                raise CommandError(
                    f"No live nb StudentUnionCategoryPage with slug {parent_slug!r}."
                )
            return parent

        count = categories.count()
        if count == 1:
            return categories.first()
        if count == 0:
            raise CommandError(
                "No live nb StudentUnionCategoryPage found to create union stubs under."
            )
        raise CommandError(
            "Multiple StudentUnionCategoryPage found -- pass --parent-slug to pick one: "
            + ", ".join(categories.values_list("slug", flat=True))
        )
