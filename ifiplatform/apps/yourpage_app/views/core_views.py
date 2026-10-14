"""Views for the event points system: the Commits page, the leaderboard, the issue
board and an issue's page (with the helpers' solution). The leaderboard and
the issues are public; the Commits page and the organiser buttons are not."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from yourpage_app.forms import GitHubLinkForm
from yourpage_app.github_sync import maybe_sync, sync
from yourpage_app.labels import (
    CATEGORY_LABELS,
    CATEGORY_SLUGS,
    SIZE_LABELS,
    difficulty_choices,
)
from yourpage_app.models import (
    DrinkTicket,
    EventIssue,
    EventSolution,
    GitHubLink,
    SyncStatus,
)
from yourpage_app.permissions import can_see_solutions, is_organiser
from yourpage_app.scoring import leaderboard, score_for


@login_required()
def main_view(request):
    """The Commits page: link your GitHub username, see your points and drink progress."""
    link = GitHubLink.objects.filter(user=request.user).first()
    if request.method == "POST":
        form = GitHubLinkForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("yourpage_main")
    else:
        form = GitHubLinkForm(
            user=request.user,
            initial={"github_login": link.github_login if link else ""},
        )

    score = score_for(link.github_login) if link else None
    assigned = []
    if link:
        open_issues = EventIssue.objects.exclude(state="CLOSED").select_related(
            "credit"
        )
        assigned = _annotate(
            [i for i in open_issues if link.github_login in i.assignees],
            can_see_solutions(request.user),
        )
        _annotate(score.issues, can_see_solutions(request.user))
    return render(
        request,
        "core/yourpage_main.html",
        {
            "form": form,
            "link": link,
            "score": score,
            "assigned_groups": [(issue, []) for issue in assigned],
            "closed_groups": [(issue, []) for issue in score.issues] if score else [],
            "drink_points": settings.DRINK_TICKET_POINTS,
            "drink_given": DrinkTicket.objects.filter(user=request.user).exists(),
        },
    )


def leaderboard_view(request):
    maybe_sync()
    linked, unlinked = leaderboard()
    organiser = is_organiser(request.user)
    status = SyncStatus.get()
    return render(
        request,
        "core/leaderboard.html",
        {
            "rows": linked,
            "unlinked": unlinked,
            "show_unlinked_names": can_see_solutions(request.user),
            "is_organiser": organiser,
            "drink_points": settings.DRINK_TICKET_POINTS,
            "status": status,
            "token_missing": organiser and not settings.GITHUB_READ_TOKEN,
            "needs_look": (
                EventIssue.objects.filter(needs_look=True) if organiser else []
            ),
        },
    )


@require_POST
def hand_out_drink_view(request, user_id):
    if not is_organiser(request.user):
        raise PermissionDenied
    user = get_object_or_404(get_user_model(), pk=user_id)
    DrinkTicket.objects.get_or_create(user=user)
    return redirect("yourpage_leaderboard")


@require_POST
def sync_now_view(request):
    if not is_organiser(request.user):
        raise PermissionDenied
    sync()
    return redirect("yourpage_leaderboard")


def _annotate(issues, show_logins):
    """Set done_by and assigned_to on each issue, as the public may see
    them: a site username where the GitHub username is linked to one;
    otherwise the GitHub username for helpers and organisers, and "" (just
    "done"/"assigned") for everyone else. done_by is None when unsolved."""
    linked_users = {
        link.github_login: link.user.get_username()
        for link in GitHubLink.objects.select_related("user")
    }

    def shown(login):
        return linked_users.get(login) or (login if show_logins else "")

    for issue in issues:
        credit = getattr(issue, "credit", None)
        issue.done_by = shown(credit.github_login) if credit else None
        names = [shown(login) for login in issue.assignees]
        issue.assigned_to = ", ".join(name for name in names if name)
        issue.is_assigned = bool(names)
    return issues


def issues_view(request):
    maybe_sync()
    issues = EventIssue.objects.select_related("credit")
    category = request.GET.get("category", "")
    difficulty = request.GET.get("difficulty", "")
    if category:
        issues = issues.filter(category=category)
    if difficulty:
        issues = issues.filter(size=difficulty)

    show_solutions = can_see_solutions(request.user)
    solution_numbers = (
        set(EventSolution.objects.values_list("issue_number", flat=True))
        if show_solutions
        else set()
    )
    issues = _annotate(list(issues), show_solutions)
    for issue in issues:
        issue.has_solution = issue.number in solution_numbers

    # Sub-issues are listed under their parent; a parent filtered out still
    # shows its matching children as their own group. Easiest first
    # everywhere, a parent (0 points itself) counting as its easiest
    # sub-issue. The grouping follows the filters: group by whichever of
    # category/difficulty is still "All" -- the visitor only chooses when
    # both are, and nothing is grouped when both are picked.
    if category and difficulty:
        group_by = ""
    elif category:
        group_by = "difficulty"
    elif difficulty:
        group_by = "category"
    else:
        group_by = (
            "difficulty" if request.GET.get("group") == "difficulty" else "category"
        )
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

    return render(
        request,
        "core/issues.html",
        {
            "open_sections": _sections(
                [g for g in groups if g[0].state != "CLOSED"], heading
            ),
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
                    all_option=False,
                    current=group_by,
                )
                if not (category or difficulty)
                else []
            ),
            "status": SyncStatus.get(),
        },
    )


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
    texts = {
        size_points: text
        for (name, text), size_points in zip(
            difficulty_choices(), sorted(p for _n, p in SIZE_LABELS.values())
        )
    }
    return texts.get(points, _("No size"))


def _pills(request, param, choices, all_option=True, current=None):
    """[(text, url, active, colour)] for one row of filter buttons -- colour
    is the category's card colour (CATEGORY_SLUGS), if any. Each link keeps
    the other filters and changes only `param`."""
    current = request.GET.get(param, "") if current is None else current
    if all_option:
        choices = [("", _("All")), *choices]
    pills = []
    for value, text in choices:
        query = request.GET.copy()
        query.pop(param, None)
        if value:
            query[param] = value
        if param != "group":
            query.pop("group", None)  # grouping only applies with both on "All"
        url = f"{request.path}?{query.urlencode()}" if query else request.path
        pills.append((text, url, value == current, CATEGORY_SLUGS.get(value, "")))
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


def issue_detail_view(request, number):
    issue = get_object_or_404(
        EventIssue.objects.select_related("credit"), number=number
    )
    show_solutions = can_see_solutions(request.user)
    _annotate([issue], show_solutions)
    return render(
        request,
        "core/issue_detail.html",
        {
            "issue": issue,
            "sub_issues": EventIssue.objects.filter(parent_number=number),
            "solution": (
                EventSolution.objects.filter(issue_number=number).first()
                if show_solutions
                else None
            ),
        },
    )
