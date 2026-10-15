"""Fills the points system with fake issues, people and points, so the
Commits page, leaderboard and issue list can be styled locally without a
GitHub token. Local only: it refuses to run unless DEBUG is on.

    python manage.py seed_fake_points                 # add the fake data
    python manage.py seed_fake_points --me <github>   # ...with some for you
    python manage.py seed_fake_points --extra 60      # ...plus 60 open issues
    python manage.py seed_fake_points --clear         # remove it again

--me takes your own GitHub username (the one linked on the Commits page):
two open issues get assigned to you and two get solved by you.

Every fake issue gets a helpers' solution: two hand-written ones (SOLUTIONS),
and a generic placeholder for the rest (fake_solution).

Fake issues are numbered from 900 and fake users are called fake_<name>
(they can't log in). A real GitHub sync replaces the fake issues and credits
with the real ones, since it rebuilds both from GitHub."""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from yourpage_app.labels import CATEGORY_LABELS, SIZE_LABELS
from yourpage_app.models import (
    Credit,
    DrinkTicket,
    EventIssue,
    EventSolution,
    GitHubLink,
)

FIRST_NUMBER = 900
EXTRA_FIRST_NUMBER = 1000
MAX_EXTRA = 500
FAKE_PREFIX = "fake_"

# (title, category index, size label, parent title or None)
ISSUES = [
    ("Make the header pumpkin orange", 0, "🍬 candy", None),
    ("Spooky font for all headings", 0, "🍫 chocolate", None),
    ("Cobwebs in the corners of the article cards", 0, "🎃 pumpkin", None),
    ("Glowing buttons", 0, "🍬 candy", None),
    ("Bats flying across the home page", 1, "🎃 pumpkin", None),
    ("Pumpkin cursor", 1, "🍬 candy", None),
    ("Countdown to Halloween on the home page", 1, "🍫 chocolate", None),
    ("Random spooky greeting template tag", 2, "🍫 chocolate", None),
    ("Write a spooky article about the IFI basement", 3, "🍫 chocolate", None),
    ("Create the costume contest event", 3, "🍬 candy", None),
    ('"Log in" becomes "Enter the crypt"', 4, "🍬 candy", None),
    ("SVG ghost icon", 5, "🍫 chocolate", None),
    ("Fix the typo in the README", 6, "🍬 candy", None),
    ("The footer is upside down", 7, "🍬 candy", None),
    ("The cards keep flickering", 7, "🍫 chocolate", None),
    ("Respect reduced motion for the bats", 8, "🍫 chocolate", None),
    ("Haunted mode", 1, None, None),
    ("Haunted mode: toggle button", 1, "🍫 chocolate", "Haunted mode"),
    ("Haunted mode: dark colours", 0, "🍬 candy", "Haunted mode"),
    ("Haunted mode: creepy sound (muted by default)", 1, "🎃 pumpkin", "Haunted mode"),
    ("Make the leaderboard spooky", 0, "🍫 chocolate", None),
    ("Add a ghost to the 404 page", 1, "🍬 candy", None),
    ("Halloween banner message", 3, "🍬 candy", None),
    ("Alt text for the new Halloween images", 8, "🍬 candy", None),
    ("Skeleton loading animation", 1, "🎃 pumpkin", None),
]

# GitHub username -> titles they solved, in the order they solved them.
PEOPLE = {
    "pumpkinqueen": [0, 4, 7, 17],
    "bytebat": [1, 5, 13],
    "ghostcoder": [2, 9, 18],
    "candycrusher": [3, 10, 12],
    "nightowl": [6, 11],
    "skeletonkey": [8],
}
UNLINKED = {"lurkinglantern": [14], "mysterymoth": [15]}
NEEDS_LOOK = [19]  # fake "one PR closed several issues"
DRINK_HANDED_OUT = ["pumpkinqueen"]
# Open issues and who they're assigned to; ME is replaced by --me.
ME = object()
ASSIGNED = {20: [ME], 21: [ME], 22: ["bytebat"], 23: ["nightowl", "lurkinglantern"]}
ME_SOLVED = [14, 15]  # credited to --me instead of UNLINKED
SOLUTIONS = {
    0: (
        "Open static/css/06_components/header.css and change the background "
        "colour to var(--color-pumpkin).\nCheck it on the home page.",
        "-  background-color: var(--color-bg-dark);\n"
        "+  background-color: var(--color-pumpkin);",
    ),
    5: (
        "Add a cursor rule to body in elements.css, pointing at an SVG in "
        "static/images/halloween/.",
        "+body {\n+  cursor: url(../images/halloween/pumpkin.svg), auto;\n+}",
    ),
}


def fake_solution(issue):
    """(note, diff) for a fake issue without a hand-written solution."""
    return (
        f'Fake solution for #{issue.number} "{issue.title}".\n'
        "Start in the template or CSS file the issue names, make the change, "
        "and check it on the page.",
        f"- <!-- TODO: #{issue.number} -->\n+ <!-- done: {issue.title} -->",
    )


class Command(BaseCommand):
    help = "Adds (or with --clear removes) fake points data for local styling."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Remove it again.")
        parser.add_argument("--me", default="", help="Your GitHub username.")
        parser.add_argument(
            "--extra", type=int, default=0, help="Extra open issues, to fill pages."
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Local only: seed_fake_points needs DEBUG=True.")
        with transaction.atomic():
            self._clear()
            if options["clear"]:
                self.stdout.write(self.style.SUCCESS("Fake points data removed."))
                return
            self._seed(options["me"].strip().lower())
            self._seed_extra(options["extra"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Added {len(ISSUES)} fake issues and {len(PEOPLE)} fake people. "
                "See /commits/leaderboard/ and /commits/issues/."
            )
        )

    def _clear(self):
        last = EXTRA_FIRST_NUMBER + MAX_EXTRA
        EventIssue.objects.filter(number__gte=FIRST_NUMBER, number__lt=last).delete()
        EventSolution.objects.filter(
            issue_number__gte=FIRST_NUMBER, issue_number__lt=last
        ).delete()
        get_user_model().objects.filter(username__startswith=FAKE_PREFIX).delete()

    def _seed(self, me):
        repo_url = f"https://github.com/{settings.GITHUB_EVENT_REPO}/issues"
        number_of = {
            title: FIRST_NUMBER + i for i, (title, *_rest) in enumerate(ISSUES)
        }
        unlinked = {me: ME_SOLVED} if me else UNLINKED
        solved = {
            i for titles in [*PEOPLE.values(), *unlinked.values()] for i in titles
        }
        assigned = {
            i: [
                me if login is ME else login
                for login in logins
                if me or login is not ME
            ]
            for i, logins in ASSIGNED.items()
        }

        issues = []
        for i, (title, category, size_label, parent) in enumerate(ISSUES):
            size, points = SIZE_LABELS.get(size_label, ("", 0))
            number = number_of[title]
            issues.append(
                EventIssue.objects.create(
                    number=number,
                    title=title,
                    url=f"{repo_url}/{number}",
                    state="CLOSED" if i in solved or i in NEEDS_LOOK else "OPEN",
                    assignees=assigned.get(i, []),
                    category=CATEGORY_LABELS[category],
                    size=size,
                    points=points,
                    parent_number=number_of[parent] if parent else None,
                    needs_look=i in NEEDS_LOOK,
                )
            )

        start = timezone.now() - timedelta(hours=2)
        minute = 0
        users = {}
        for login, solved_titles in [*PEOPLE.items(), *unlinked.items()]:
            for index in solved_titles:
                minute += 7
                Credit.objects.create(
                    issue=issues[index],
                    github_login=login,
                    pr_number=issues[index].number + 100,
                    credited_at=start + timedelta(minutes=minute),
                )
            if login in PEOPLE:
                user = get_user_model().objects.create_user(
                    username=f"{FAKE_PREFIX}{login}", password=None
                )
                GitHubLink.objects.create(user=user, github_login=login)
                users[login] = user

        for login in DRINK_HANDED_OUT:
            DrinkTicket.objects.create(user=users[login])
        for index, issue in enumerate(issues):
            note, diff = SOLUTIONS.get(index) or fake_solution(issue)
            EventSolution.objects.create(
                issue_number=issue.number, note=note, diff=diff
            )

    def _seed_extra(self, count):
        """`count` plain open issues, spread over every category and size."""
        repo_url = f"https://github.com/{settings.GITHUB_EVENT_REPO}/issues"
        sizes = list(SIZE_LABELS.values())
        for i in range(min(count, MAX_EXTRA)):
            size, points = sizes[i % len(sizes)]
            number = EXTRA_FIRST_NUMBER + i
            issue = EventIssue.objects.create(
                number=number,
                title=f"Extra spooky task {i + 1}",
                url=f"{repo_url}/{number}",
                state="OPEN",
                category=CATEGORY_LABELS[i % len(CATEGORY_LABELS)],
                size=size,
                points=points,
            )
            note, diff = fake_solution(issue)
            EventSolution.objects.create(issue_number=number, note=note, diff=diff)
