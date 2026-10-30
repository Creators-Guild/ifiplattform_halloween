"""Prints the anonymous totals Hanna's thesis takes from the mock site before
it's deleted, as CSV on stdout (plan: docs/claude_plans/
halloween_mock_site_totals.md). Read-only. Only totals, never anything per
account: that is what Sikt and the participants were promised.

    docker compose exec -T web python manage.py halloween_totals > halloween_totals.csv
"""

import csv
from datetime import datetime
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from commits_app.models import Claim, Credit, CreditOverride, GitHubLink

# Org and helper accounts: not participants. Whole username, any case.
EXCLUDED_USERNAMES = [
    "admin",
    "andreval",
    "halloween-admin",
    "arin",
    "attilaac",
    "geiteadmin",
    "stefanna",
    "whistler",
    "test",
]


class Command(BaseCommand):
    help = "Prints the mock site's anonymous totals as CSV (read-only)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--also-exclude",
            nargs="*",
            default=[],
            metavar="USERNAME",
            help="More org/helper usernames to leave out, once Hanna has said so.",
        )

    def handle(self, *args, **options):
        excluded_names = {
            name.lower() for name in EXCLUDED_USERNAMES + options["also_exclude"]
        }
        users = get_user_model().objects.all()
        excluded_ids = {
            pk for pk, name in users.values_list("pk", "username")
            if name.lower() in excluded_names
        }
        participants = users.exclude(pk__in=excluded_ids)

        unlisted_staff = participants.filter(Q(is_staff=True) | Q(is_superuser=True))
        if unlisted_staff.exists():
            raise CommandError(
                f"{unlisted_staff.count()} staff/superuser account(s) not on the "
                "exclude list. Ask Hanna, then rerun with --also-exclude if they "
                "should be left out. No CSV written."
            )

        links = dict(GitHubLink.objects.values_list("user_id", "github_login"))
        excluded_logins = {links[pk] for pk in excluded_ids if pk in links}
        credits = list(
            Credit.objects.exclude(github_login__in=excluded_logins).values_list(
                "issue__number", "github_login", "pr_number"
            )
        )
        credited_logins = {login for _, login, _ in credits}

        # Which rule gave each credit, checked in _credit's order
        # (github_sync.py), against the overrides and claims as they are now.
        overrides = set(CreditOverride.objects.values_list("issue_number", flat=True))
        claimed_by = {
            number: links.get(user_id)
            for number, user_id in Claim.objects.values_list("issue_number", "user_id")
        }
        by_override = by_claim = by_claim_without_pr = by_github = 0
        for number, login, pr_number in credits:
            if number in overrides:
                by_override += 1
            elif claimed_by.get(number) == login:
                by_claim += 1
                by_claim_without_pr += pr_number is None
            else:
                by_github += 1

        participant_ids = set(participants.values_list("pk", flat=True))
        linked_ids = participant_ids & links.keys()
        claimer_ids = set(Claim.objects.values_list("user_id", flat=True))
        rows = [
            (
                "accounts_total",
                len(participant_ids),
                "all site accounts, active or not, minus accounts_excluded",
            ),
            (
                "accounts_github_connected",
                len(linked_ids),
                "commits_app.GitHubLink: a GitHub username typed on the Commits page",
            ),
            (
                "accounts_solved_task",
                sum(links[pk] in credited_logins for pk in linked_ids),
                "linked GitHub username has at least one Credit row "
                "(what Your Page and the leaderboard showed as solved)",
            ),
            (
                "accounts_did_nothing",
                len(participant_ids - linked_ids - claimer_ids),
                "no GitHubLink and never claimed an issue (Claim)",
            ),
            (
                "accounts_excluded",
                len(excluded_ids),
                "org/helper accounts on the plan's list",
            ),
            (
                "issues_credited",
                len(credits),
                "issues that gave points, excluded accounts left out",
            ),
            ("issues_credited_by_override", by_override, "organiser CreditOverride"),
            ("issues_credited_by_claim", by_claim, "claimed on the site"),
            (
                "issues_credited_by_claim_without_pr",
                by_claim_without_pr,
                "claimed, no merged PR",
            ),
            (
                "issues_credited_by_github",
                by_github,
                "merged PR author or first assignee",
            ),
            ("peoply_signups", "", "Peoply event page, read by hand"),
            (
                "taken_at",
                datetime.now(ZoneInfo("Europe/Oslo")).isoformat(timespec="minutes"),
                "",
            ),
            ("commit", "", "mock site repo, code that counted"),
        ]
        writer = csv.writer(self.stdout, lineterminator="\n")
        writer.writerow(["measure", "value", "definition"])
        writer.writerows(rows)
