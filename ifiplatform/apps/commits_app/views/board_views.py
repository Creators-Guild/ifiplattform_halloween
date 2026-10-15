"""The issue board: every event issue as cards, filtered by category and
difficulty, grouped into sections, with free issues first in each
visitor's own shuffled order."""

from django.conf import settings
from django.shortcuts import render
from django.utils.translation import gettext as _

from commits_app import claims
from commits_app.github_sync import maybe_sync
from commits_app.labels import (
    CATEGORY_LABELS,
    CATEGORY_SLUGS,
    SIZE_LABELS,
    difficulty_choices,
    difficulty_text,
)
from commits_app.models import EventIssue, GitHubLink, SyncStatus

from .common import annotate


def issues_view(request):
    maybe_sync()
    claims.release_expired()
    issues = EventIssue.objects.select_related("credit")
    categories = _picked(request, "category")
    difficulties = _picked(request, "difficulty")
    if categories:
        issues = issues.filter(category__in=categories)
    if difficulties:
        issues = issues.filter(size__in=difficulties)

    issues = annotate(list(issues), request.user)

    # Sub-issues are listed under their parent; a parent filtered out still
    # shows its matching children as their own group. Easiest first
    # everywhere, a parent (0 points itself) counting as its easiest
    # sub-issue. The grouping follows the filters: only a filter that still
    # spans several values ("All", or more than one picked) is worth
    # grouping by. The visitor chooses when both do; nothing is grouped
    # when each filter is down to one value.
    can_group = {
        "category": len(categories) != 1,
        "difficulty": len(difficulties) != 1,
    }
    if all(can_group.values()):
        group_by = (
            "difficulty" if request.GET.get("group") == "difficulty" else "category"
        )
    else:
        group_by = next((key for key, ok in can_group.items() if ok), "")
    issues = sorted(issues, key=lambda i: (i.points, i.number))
    shown = {issue.number for issue in issues}
    children = {}
    for issue in issues:
        if issue.parent_number in shown:
            children.setdefault(issue.parent_number, []).append(issue)
    groups = [
        (issue, children.get(issue.number, []))
        for issue in issues
        if issue.parent_number not in shown
    ]
    groups.sort(key=_difficulty_key)
    if group_by == "category":
        groups.sort(key=_category_key)  # stable: easiest first within a category
    heading = {
        "category": _category_heading,
        "difficulty": _difficulty_heading,
    }.get(group_by, lambda group: "")
    open_groups = _free_first(
        [g for g in groups if g[0].state != "CLOSED"], heading, request.user
    )
    linked = GitHubLink.objects.filter(user_id=request.user.pk).exists()
    held = claims.held_numbers(request.user) if linked else []

    return render(
        request,
        "core/issues.html",
        {
            "open_sections": _sections(open_groups, heading),
            "closed_sections": _sections(
                [g for g in groups if g[0].state == "CLOSED"], heading
            ),
            "category_pills": _pills(
                request, "category", [(c, c) for c in CATEGORY_LABELS]
            ),
            "difficulty_pills": _pills(request, "difficulty", difficulty_choices()),
            "group_pills": (
                _pills(
                    request,
                    "group",
                    [("category", _("Category")), ("difficulty", _("Difficulty"))],
                    multi=False,
                    current=group_by,
                )
                if all(can_group.values())
                else []
            ),
            "status": SyncStatus.get(),
            "can_claim": linked,
            "held_numbers": ", ".join(f"#{n}" for n in held),
            "at_limit": len(held) >= settings.CLAIM_LIMIT,
            "claim_limit": settings.CLAIM_LIMIT,
            "lucky_sizes": difficulty_choices(),
            "lucky_categories": CATEGORY_LABELS,
        },
    )


def _group_taken(group):
    """A parent counts as taken when all of its sub-issues are."""
    issue, sub_issues = group
    if sub_issues and not issue.points:
        return all(s.is_taken for s in sub_issues)
    return issue.is_taken


def _free_first(groups, heading, user):
    """Within each section, free issues before taken ones, and for a logged-in
    visitor in their own stable shuffled order (claims.shuffle_key), so not
    everyone goes for the same first card. Sections keep their order.
    Logged-out visitors keep the easiest-first order."""
    first_seen = {}
    keyed = []
    for position, group in enumerate(groups):
        section = first_seen.setdefault(heading(group), len(first_seen))
        shuffle = (
            claims.shuffle_key(user.pk, group[0].number)
            if user.is_authenticated
            else position
        )
        keyed.append(((section, _group_taken(group), shuffle), group))
    return [group for _key, group in sorted(keyed, key=lambda pair: pair[0])]


def _difficulty_key(group):
    issue, sub_issues = group
    return (min((s.points for s in sub_issues), default=issue.points), issue.number)


def _group_category(group):
    issue, sub_issues = group
    return issue.category or next((s.category for s in sub_issues), "")


def _category_key(group):
    category = _group_category(group)
    if category in CATEGORY_LABELS:
        return CATEGORY_LABELS.index(category)
    return len(CATEGORY_LABELS)


def _category_heading(group):
    return _group_category(group) or _("No category")


def _difficulty_heading(group):
    points = _difficulty_key(group)[0]
    size = next((name for name, p in SIZE_LABELS.values() if p == points), "")
    return difficulty_text(size) or _("No size")


def _picked(request, param):
    """The values picked in a multi-select filter, once each, in URL order."""
    return list(dict.fromkeys(v for v in request.GET.getlist(param) if v))


def _pills(request, param, choices, multi=True, current=None):
    """[(text, url, active, colour)] for one row of filter buttons -- colour
    is the category's card colour (CATEGORY_SLUGS), if any. Each link keeps
    the other filters and changes only `param`. A multi-select row starts
    with "All", which clears it, and each pill toggles its own value in or
    out; the Group by row (multi=False) picks exactly one value."""
    picked = _picked(request, param) if multi else [current]
    if multi:
        choices = [("", _("All")), *choices]
    pills = []
    for value, text in choices:
        if not value:
            values, active = [], not picked
        elif not multi:
            values, active = [value], value == current
        elif value in picked:
            values, active = [v for v in picked if v != value], True
        else:
            values, active = [*picked, value], False
        query = request.GET.copy()
        if values:
            query.setlist(param, values)
        else:
            query.pop(param, None)
        url = f"{request.path}?{query.urlencode()}" if query else request.path
        pills.append((text, url, active, CATEGORY_SLUGS.get(value, "")))
    return pills


def _sections(groups, heading):
    """[(heading, groups)], in the order the sorted groups already have, so
    the page can draw a titled section per category or difficulty."""
    sections = []
    for group in groups:
        title = heading(group)
        if not sections or sections[-1][0] != title:
            sections.append((title, []))
        sections[-1][1].append(group)
    return sections
