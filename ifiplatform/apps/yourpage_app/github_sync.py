"""Copies the event issues and who solved them from GitHub into EventIssue and
Credit. Run by `manage.py sync_github_points` (after every deploy, see
deploy/docker/deploy.sh) and lazily by the leaderboard and issue board via
maybe_sync(), at most once a minute.

Only public data is asked for: issue numbers, titles, labels and states, PR
numbers, and GitHub usernames (`login`, never any other profile field).

Credit rules, for an issue with a size label and no sub-issues:
1. A CreditOverride, if an organiser made one.
2. Otherwise, if the issue is closed as completed: the author of the
   earliest merged PR that closes it, else its first assignee.
A merged PR that closes more than one event issue earns none of them; those
issues get needs_look, and an organiser settles them with a CreditOverride.
"""

import json
import logging
import urllib.error
import urllib.request
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from .labels import CATEGORY_LABELS, SIZE_LABELS
from .models import Credit, CreditOverride, EventIssue, SyncStatus

logger = logging.getLogger(__name__)

GRAPHQL_URL = "https://api.github.com/graphql"
TIMEOUT_SECONDS = 10
SYNC_LOCK_KEY = "github_sync_lock"
SYNC_INTERVAL_SECONDS = 60

QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 100, after: $cursor, orderBy: {field: CREATED_AT, direction: ASC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title url state stateReason closedAt
        labels(first: 20) { nodes { name } }
        parent { number }
        assignees(first: 5) { nodes { login } }
        closedByPullRequestsReferences(first: 10, includeClosedPrs: true) {
          nodes { number merged mergedAt author { login } }
        }
      }
    }
  }
}
"""


class SyncError(Exception):
    """GitHub couldn't be reached or answered with an error."""


def _post(variables):
    request = urllib.request.Request(
        GRAPHQL_URL,
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers={
            "Authorization": f"Bearer {settings.GITHUB_READ_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "ifiplattform-halloween-points",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = json.load(response)
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise SyncError(f"GitHub request failed: {exc}") from exc
    if body.get("errors"):
        raise SyncError(f"GitHub answered with errors: {body['errors']}")
    repository = (body.get("data") or {}).get("repository")
    if repository is None:
        raise SyncError(f"Repository {settings.GITHUB_EVENT_REPO} not found")
    return repository["issues"]


def fetch_issues():
    """Every issue in the event repo, as GitHub's raw dicts."""
    owner, name = settings.GITHUB_EVENT_REPO.split("/", 1)
    issues, cursor = [], None
    while True:
        page = _post({"owner": owner, "name": name, "cursor": cursor})
        issues += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            return issues
        cursor = page["pageInfo"]["endCursor"]


def _parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def _labels(raw):
    return [label["name"] for label in raw["labels"]["nodes"]]


def _merged_prs(raw):
    return [
        pr
        for pr in raw["closedByPullRequestsReferences"]["nodes"]
        if pr["merged"] and pr.get("author")
    ]


def apply(raw_issues):
    """Rewrite EventIssue and Credit from GitHub's issue dicts. Separate from
    fetching so tests can feed it data directly."""
    sized = {
        raw["number"]: raw
        for raw in raw_issues
        if any(label in SIZE_LABELS for label in _labels(raw))
    }
    parent_numbers = {
        raw["parent"]["number"] for raw in sized.values() if raw.get("parent")
    }
    by_number = {raw["number"]: raw for raw in raw_issues}
    kept = {
        number: by_number[number]
        for number in sized.keys() | parent_numbers
        if number in by_number
    }
    # Leaves are the issues that earn points: sized, with no sized children.
    leaves = {
        number: raw for number, raw in sized.items() if number not in parent_numbers
    }

    # Which event issues each merged PR closes, for the abuse guard.
    closes = {}
    for number, raw in leaves.items():
        for pr in _merged_prs(raw):
            closes.setdefault(pr["number"], set()).add(number)
    greedy_prs = {pr for pr, numbers in closes.items() if len(numbers) > 1}

    overrides = dict(CreditOverride.objects.values_list("issue_number", "github_login"))

    with transaction.atomic():
        EventIssue.objects.exclude(number__in=kept).delete()
        Credit.objects.all().delete()
        for number, raw in kept.items():
            labels = _labels(raw)
            size, points = next(
                (SIZE_LABELS[label] for label in labels if label in SIZE_LABELS),
                ("", 0),
            )
            is_leaf = number in leaves
            merged = _merged_prs(raw) if is_leaf else []
            issue, _ = EventIssue.objects.update_or_create(
                number=number,
                defaults={
                    "title": raw["title"],
                    "url": raw["url"],
                    "state": raw["state"],
                    "category": next(
                        (label for label in labels if label in CATEGORY_LABELS), ""
                    ),
                    "size": size if is_leaf else "",
                    "points": points if is_leaf else 0,
                    "parent_number": (raw.get("parent") or {}).get("number"),
                    "assignees": [
                        a["login"].lower() for a in raw["assignees"]["nodes"]
                    ],
                    "needs_look": any(pr["number"] in greedy_prs for pr in merged),
                },
            )
            if is_leaf:
                _credit(issue, raw, merged, greedy_prs, overrides.get(number))
    return len(kept)


def _credit(issue, raw, merged, greedy_prs, override_login):
    closed_at = _parse_time(raw.get("closedAt"))
    if override_login:
        Credit.objects.create(
            issue=issue,
            github_login=override_login,
            credited_at=closed_at or timezone.now(),
        )
        return
    if raw["state"] != "CLOSED" or raw.get("stateReason") != "COMPLETED":
        return
    if merged:
        if any(pr["number"] in greedy_prs for pr in merged):
            return
        pr = min(merged, key=lambda pr: pr["mergedAt"])
        Credit.objects.create(
            issue=issue,
            github_login=pr["author"]["login"].lower(),
            pr_number=pr["number"],
            credited_at=_parse_time(pr["mergedAt"]),
        )
        return
    assignees = raw["assignees"]["nodes"]
    if assignees:
        Credit.objects.create(
            issue=issue,
            github_login=assignees[0]["login"].lower(),
            credited_at=closed_at or timezone.now(),
        )


def sync():
    """Fetch and apply, recording the outcome in SyncStatus. Never raises:
    a failure keeps the old data and is logged. Returns True on success."""
    status = SyncStatus.get()
    status.last_attempt_at = timezone.now()
    if not settings.GITHUB_READ_TOKEN:
        status.last_error = "GITHUB_READ_TOKEN is not set."
        status.save()
        return False
    try:
        count = apply(fetch_issues())
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # Broad on purpose: the lazy sync runs inside page views, which must
        # keep working whatever GitHub (or its data) does.
        logger.warning("GitHub points sync failed: %s", exc)
        status.last_error = str(exc)[:2000]
        status.save()
        return False
    status.last_success_at = status.last_attempt_at
    status.last_error = ""
    status.save()
    logger.info("GitHub points sync: %s event issue(s)", count)
    return True


def maybe_sync():
    """Sync if a token is set and nobody has in the last minute. The lock is
    in the file cache, which every Gunicorn worker shares."""
    if settings.GITHUB_READ_TOKEN and cache.add(
        SYNC_LOCK_KEY, 1, SYNC_INTERVAL_SECONDS
    ):
        sync()
