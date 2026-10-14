"""Occasional helper for populating peoply_organization_id across every
real UnionPage on this environment -- unlike seed_dev_data, which
deliberately only sets it for 2 example unions (see that file's own
comment, FADDERUKE_UNION_PEOPLY_IDS), this is meant to cover all of them
here, once, per environment (i.e. production).

For each live nb UnionPage without a peoply_organization_id yet, queries
Peoply's own name search (?name=) for candidates, then only accepts an
EXACT case-insensitive match against either the org's display name or its
urlId (Peoply's own shorthand, e.g. "cyb" for "Cybernetisk Selskab") --
confirmed the hard way that Peoply's search is substring-based, not exact
(querying "FU" returns "FUI", an unrelated real union) -- so a naive
first-result match would risk silently linking a union to someone else's
events. Anything without an exact match is reported, not guessed at.

Dry run by default -- unlike most of this project's commands, this one
flips that default deliberately, since a wrong automated match would
misattribute a whole union's worth of events. Pass --apply to actually
write peoply_organization_id."""

import requests
from django.core.management.base import BaseCommand

from ifi_home_app.integrations.peoply_api import apply_peoply_match, find_exact_match
from ifi_home_app.models.article.unions import UnionPage

PEOPLY_ORGANIZATIONS_URL = "https://api.peoply.app/organizations"


class Command(BaseCommand):
    help = (
        "Matches every live UnionPage (missing a peoply_organization_id) "
        "against Peoply's organizations by exact name/urlId, and reports "
        "(or, with --apply, writes) each match. Dry run by default."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write peoply_organization_id for matched unions. Without this, only prints proposed matches.",
        )

    def handle(self, *args, **options):
        unions = (
            UnionPage.objects.live()
            .filter(locale__language_code="nb", peoply_organization_id="")
            .order_by("title")
        )

        matched = []
        unmatched = []

        for union in unions:
            try:
                response = requests.get(
                    PEOPLY_ORGANIZATIONS_URL, params={"name": union.title}, timeout=10
                )
                response.raise_for_status()
            except requests.RequestException as exc:
                self.stderr.write(f"  {union.title}: request failed ({exc})")
                unmatched.append(union.title)
                continue

            org = find_exact_match(union.title, response.json())
            if org:
                matched.append((union, org))
            else:
                unmatched.append(union.title)

        if matched:
            self.stdout.write(self.style.SUCCESS(f"Matched {len(matched)}:"))
            for union, org in matched:
                self.stdout.write(f"  {union.title!r} -> {org['name']!r} ({org['id']})")

        if unmatched:
            self.stdout.write(
                self.style.WARNING(
                    f"No confident match for {len(unmatched)} union(s) -- look these up "
                    f"by hand on peoply.app and set peoply_organization_id directly: "
                    + ", ".join(unmatched)
                )
            )

        if not options["apply"]:
            self.stdout.write(
                "Dry run -- nothing written. Re-run with --apply to save these matches."
            )
            return

        for union, org in matched:
            apply_peoply_match(union, org)
        self.stdout.write(self.style.SUCCESS(f"Applied {len(matched)} match(es)."))
