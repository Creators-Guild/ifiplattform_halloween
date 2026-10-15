"""Claiming issues on the Commits pages: one click instead of a GitHub comment
and a helper's assignment.

- Anyone with a linked GitHub username may hold CLAIM_LIMIT open issues,
  counting both their claims and the issues assigned to them on GitHub.
- A claim runs out after CLAIM_MINUTES for its size (settings.py), unless
  the claimer clicks "Keep". Helpers can add time, remove the limit or
  reset it (adjust), or force-release it. Once the sync sees an open PR by
  the claimer, their claims get no time limit (lock_for), so a claim can't
  run out between the merge and someone closing the issue.
- An issue is free when it's open, worth points, not assigned on GitHub,
  and not claimed.
- Claims on closed issues are history: the sync credits the claimer when a
  claimed issue is closed as completed, so nothing here ever deletes them.
"""

import hashlib
import math
import random
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Claim, EventIssue, GitHubLink

DEFAULT_MINUTES = 60
EXTRA_MINUTES = {"plus15": 15, "plus30": 30}
ADJUST_ACTIONS = [*EXTRA_MINUTES, "unlimited", "reset"]


def default_minutes(issue):
    return settings.CLAIM_MINUTES.get(issue.size, DEFAULT_MINUTES)


def _open_numbers():
    return EventIssue.objects.exclude(state="CLOSED").values("number")


def open_claims(user):
    return Claim.objects.filter(user=user, issue_number__in=_open_numbers())


def held_numbers(user):
    """The open issues this person holds, which is what CLAIM_LIMIT counts:
    their claims here and the issues assigned to them on GitHub (the same
    ones My issues lists under "Your issues")."""
    numbers = set(open_claims(user).values_list("issue_number", flat=True))
    link = GitHubLink.objects.filter(user=user).first()
    if link:
        numbers |= {
            i.number
            for i in EventIssue.objects.exclude(state="CLOSED")
            if link.github_login in i.assignees
        }
    return sorted(numbers)


def release_expired():
    """Free every claim on an open issue whose time has run out. Called at
    the start of each Commits page, so no scheduler is needed."""
    Claim.objects.filter(
        issue_number__in=_open_numbers(), expires_at__lt=timezone.now()
    ).delete()


def lock_for(logins):
    """No time limit on the open claims of these GitHub usernames (the ones
    with an open PR, from the sync)."""
    Claim.objects.filter(
        issue_number__in=_open_numbers(),
        user__github_link__github_login__in=logins,
    ).update(expires_at=None)


def free_issues():
    """Open issues worth points that nobody holds, on the site or on GitHub."""
    claimed = Claim.objects.values("issue_number")
    issues = EventIssue.objects.exclude(state="CLOSED").filter(points__gt=0)
    return [i for i in issues.exclude(number__in=claimed) if not i.assignees]


def claim(user, issue):
    """(Claim, "ok"), or (None, reason): "unlinked", "not_claimable",
    "taken" or "limit". Safe when two people click at once (the unique
    issue number) and when one person clicks two cards at once (the lock on
    their GitHubLink row while counting)."""
    link = GitHubLink.objects.filter(user=user).first()
    if not link:
        return None, "unlinked"
    if issue.state == "CLOSED" or not issue.points:
        return None, "not_claimable"
    if issue.assignees or Claim.objects.filter(issue_number=issue.number).exists():
        return None, "taken"
    try:
        with transaction.atomic():
            GitHubLink.objects.select_for_update().get(pk=link.pk)
            if len(held_numbers(user)) >= settings.CLAIM_LIMIT:
                return None, "limit"
            new = Claim.objects.create(
                issue_number=issue.number,
                user=user,
                expires_at=timezone.now() + timedelta(minutes=default_minutes(issue)),
            )
    except IntegrityError:
        return None, "taken"
    return new, "ok"


def alternative(issue):
    """A random free issue like this one: same size and category, else the
    same size, else any. None when nothing is free."""
    free = [i for i in free_issues() if i.number != issue.number]
    for candidates in (
        [i for i in free if i.size == issue.size and i.category == issue.category],
        [i for i in free if i.size == issue.size],
        free,
    ):
        if candidates:
            return random.choice(candidates)
    return None


def random_free(size="", category="", skip=None):
    """ "Give me an issue": a random free issue matching the filters, or None.
    It only picks; claiming is the visitor's choice. `skip` is the one just
    shown, so "Try another" gives a different one when there is one."""
    candidates = [
        i
        for i in free_issues()
        if (not size or i.size == size) and (not category or i.category == category)
    ]
    others = [i for i in candidates if i.number != skip]
    pool = others or candidates
    return random.choice(pool) if pool else None


def is_open(claim_):
    return (
        EventIssue.objects.filter(number=claim_.issue_number)
        .exclude(state="CLOSED")
        .exists()
    )


def keep(claim_, issue):
    """The claimer's "Keep": the full default time again, from now."""
    claim_.expires_at = timezone.now() + timedelta(minutes=default_minutes(issue))
    claim_.save(update_fields=["expires_at"])


def adjust(claim_, issue, action):
    """A helper's change to one claim's time."""
    now = timezone.now()
    if action in EXTRA_MINUTES:
        start = max(claim_.expires_at or now, now)
        claim_.expires_at = start + timedelta(minutes=EXTRA_MINUTES[action])
    elif action == "unlimited":
        claim_.expires_at = None
    else:
        claim_.expires_at = now + timedelta(minutes=default_minutes(issue))
    claim_.save(update_fields=["expires_at"])


def minutes_left(claim_):
    """Whole minutes until the claim runs out, or None for no time limit."""
    if claim_.expires_at is None:
        return None
    return max(0, math.ceil((claim_.expires_at - timezone.now()).total_seconds() / 60))


def shuffle_key(seed, number):
    """The same random-looking position for the same person and issue every
    time, and a different order for every person."""
    return int(hashlib.sha256(f"{seed}:{number}".encode()).hexdigest()[:12], 16)
