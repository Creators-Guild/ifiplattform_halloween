"""Views for the event points system: the Commits page, the leaderboard, the issue
board and an issue's page (with the helpers' solution), and the claim buttons
(rules in claims.py). The leaderboard and the issues are public; the Commits
page, claiming and the organiser buttons are not."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from commits_app import claims
from commits_app.forms import GitHubLinkForm
from commits_app.github_sync import maybe_sync, sync
from commits_app.labels import (
    CATEGORY_LABELS,
    CATEGORY_SLUGS,
    SIZE_LABELS,
    difficulty_choices,
)
from commits_app.models import (
    Claim,
    DrinkTicket,
    EventIssue,
    EventSolution,
    GitHubLink,
    SyncStatus,
)
from commits_app.permissions import can_see_solutions, is_organiser
from commits_app.scoring import leaderboard, score_for


@login_required()
def main_view(request):
    """The Commits page: link your GitHub username, see your points and drink progress."""
    link = GitHubLink.objects.filter(user=request.user).first()
    if request.method == "POST":
        form = GitHubLinkForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("commits_main")
    else:
        form = GitHubLinkForm(
            user=request.user,
            initial={"github_login": link.github_login if link else ""},
        )

    claims.release_expired()
    score = score_for(link.github_login) if link else None
    mine = []
    if link:
        open_issues = _annotate(
            list(EventIssue.objects.exclude(state="CLOSED").select_related("credit")),
            request.user,
        )
        # Claimed here or assigned on GitHub: both are yours.
        mine = [i for i in open_issues if i.is_mine or link.github_login in i.assignees]
        _annotate(score.issues, request.user)
    return render(
        request,
        "core/commits_main.html",
        {
            "form": form,
            "link": link,
            "score": score,
            "assigned_groups": [(issue, []) for issue in mine],
            "closed_groups": [(issue, []) for issue in score.issues] if score else [],
            "drink_points": settings.DRINK_TICKET_POINTS,
            "drink_given": DrinkTicket.objects.filter(user=request.user).exists(),
        },
    )


def leaderboard_view(request):
    maybe_sync()
    claims.release_expired()
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
    return redirect("commits_leaderboard")


@require_POST
def sync_now_view(request):
    """The tab bar's Sync now (helpers and organisers): fetch from GitHub
    now instead of waiting for the once-a-minute sync."""
    if not can_see_solutions(request.user):
        raise PermissionDenied
    if sync():
        messages.success(request, _("Synced from GitHub."), extra_tags="claim claim-ok")
    else:
        messages.warning(
            request,
            _("Sync failed: %(error)s") % {"error": SyncStatus.get().last_error},
            extra_tags="claim claim-limit",
        )
    return _back(request)


def _annotate(issues, user):
    """Set what the cards show, as this visitor may see it.

    done_by and assigned_to: a site username where the GitHub username is
    linked to one; otherwise the GitHub username for helpers and organisers
    (can_see_solutions), and "" (just "done"/"assigned") for everyone else.
    done_by is None when unsolved.

    show_solution (helpers get a solution button on every issue) and
    has_solution (whether it finds one or says it's missing).

    Claims (claims.py): claim, claimed_by, is_mine, assigned_to_me (on
    GitHub, which the site can't undo: the card says so), is_new (yours and
    not opened yet: highlighted on My issues), minutes_left,
    claim_default (for the helper box), can_claim (the visitor may press
    Claim: linked, and the issue is free), and is_taken (someone else holds
    it, here or on GitHub)."""
    for_helper = can_see_solutions(user)
    links = list(GitHubLink.objects.select_related("user"))
    linked_users = {link.github_login: link.user.get_username() for link in links}
    my_login = next(
        (link.github_login for link in links if link.user_id == user.pk), None
    )
    solution_numbers = (
        set(EventSolution.objects.values_list("issue_number", flat=True))
        if for_helper
        else set()
    )
    claim_of = {c.issue_number: c for c in Claim.objects.select_related("user")}

    def shown(login):
        return linked_users.get(login) or (login if for_helper else "")

    for issue in issues:
        credit = getattr(issue, "credit", None)
        issue.done_by = shown(credit.github_login) if credit else None
        names = [shown(login) for login in issue.assignees]
        issue.assigned_to = ", ".join(name for name in names if name)
        issue.is_assigned = bool(names)
        issue.show_solution = for_helper
        issue.has_solution = issue.number in solution_numbers

        claim = claim_of.get(issue.number)
        is_open = issue.state != "CLOSED"
        issue.claim = claim
        issue.claimed_by = claim.user.get_username() if claim else ""
        issue.is_mine = bool(claim and claim.user_id == user.pk)
        issue.assigned_to_me = bool(my_login and my_login in issue.assignees)
        issue.is_new = bool(issue.is_mine and claim.seen_at is None)
        issue.minutes_left = claims.minutes_left(claim) if claim else None
        issue.claim_default = claims.default_minutes(issue)
        issue.can_claim = bool(
            my_login and is_open and issue.points and not claim and not names
        )
        issue.is_taken = is_open and (
            (claim is not None and not issue.is_mine)
            or (claim is None and bool(names) and my_login not in issue.assignees)
        )
    return issues


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

    issues = _annotate(list(issues), request.user)

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
    texts = {
        size_points: text
        for (name, text), size_points in zip(
            difficulty_choices(), sorted(p for _n, p in SIZE_LABELS.values())
        )
    }
    return texts.get(points, _("No size"))


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


def issue_detail_view(request, number):
    claims.release_expired()
    issue = get_object_or_404(
        EventIssue.objects.select_related("credit"), number=number
    )
    show_solutions = can_see_solutions(request.user)
    _annotate([issue], request.user)
    if issue.is_new:  # the claimer's first look ends the highlight on My issues
        Claim.objects.filter(pk=issue.claim.pk).update(seen_at=timezone.now())
    credit = getattr(issue, "credit", None)
    # The repo's URL is the issue's minus "/issues/<n>"; PRs live beside it.
    pr_url = (
        f"{issue.url.rsplit('/issues/', 1)[0]}/pull/{credit.pr_number}"
        if credit and credit.pr_number
        else ""
    )
    return render(
        request,
        "core/issue_detail.html",
        {
            "issue": issue,
            "parent": (
                EventIssue.objects.filter(number=issue.parent_number).first()
                if issue.parent_number
                else None
            ),
            "credit": credit,
            "pr_url": pr_url,
            # Came from "Give me an issue": the panel offers "Try another".
            "lucky_query": (
                urlencode(
                    dict(
                        zip(("size", "category"), _lucky_filters(request)),
                        skip=number,
                    )
                )
                if request.GET.get("lucky")
                else ""
            ),
            "sub_issues": _annotate(
                list(EventIssue.objects.filter(parent_number=number)), request.user
            ),
            "solution": (
                EventSolution.objects.filter(issue_number=number).first()
                if show_solutions
                else None
            ),
        },
    )


def _back(request):
    """Back to the page the button was on (the list behind a pop-up, or an
    issue's own page), else the issue list."""
    referer = request.META.get("HTTP_REFERER", "")
    if url_has_allowed_host_and_scheme(
        referer, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(referer)
    return redirect("commits_issues")


def _claim_message(request, issue, new, reason):
    """The message after Claim or "Give me an issue". Tags start with
    "claim" so core/messages.html can style them; claim-got adds a link to
    My issues, and claim-offer-<n> a button for a similar free issue."""
    if reason == "ok":
        messages.success(
            request,
            _(
                "#%(number)s is yours! %(title)s. When the issue is closed, "
                "the points come to you automatically."
            )
            % {"number": issue.number, "title": issue.title},
            extra_tags="claim claim-ok claim-got",
        )
    elif reason == "taken":
        holder = Claim.objects.filter(issue_number=issue.number).first()
        offer = claims.alternative(issue)
        text = (
            _("Just taken by %(name)s.") % {"name": holder.user.get_username()}
            if holder
            else _("Someone already has this one.")
        )
        if offer:
            text += " " + _("How about #%(number)s %(title)s?") % {
                "number": offer.number,
                "title": offer.title,
            }
        tags = "claim claim-taken" + (f" claim-offer-{offer.number}" if offer else "")
        messages.warning(request, text, extra_tags=tags)
    elif reason == "limit":
        numbers = ", ".join(f"#{n}" for n in claims.held_numbers(request.user))
        messages.warning(
            request,
            _(
                "You already have %(count)s issues (%(numbers)s). Finish or release "
                "one to claim another. Pull request merged? Ask a helper to close "
                "the issue."
            )
            % {"count": settings.CLAIM_LIMIT, "numbers": numbers},
            extra_tags="claim claim-limit",
        )
    elif reason == "unlinked":
        messages.warning(
            request,
            _("Link your GitHub username on My issues to claim issues."),
            extra_tags="claim claim-limit",
        )
    elif reason == "none_free":
        messages.warning(
            request,
            _("No free issues match. Try any difficulty or category."),
            extra_tags="claim claim-limit",
        )
    else:
        messages.warning(
            request,
            _("#%(number)s can't be claimed.") % {"number": issue.number},
            extra_tags="claim claim-limit",
        )


@login_required()
@require_POST
def claim_view(request, number):
    claims.release_expired()
    issue = get_object_or_404(EventIssue, number=number)
    new, reason = claims.claim(request.user, issue)
    _claim_message(request, issue, new, reason)
    return _back(request)


def _lucky_filters(request):
    """The size and category picked in "Give me an issue" ("" means any),
    ignoring anything that isn't a real one."""
    size = request.GET.get("size", "")
    category = request.GET.get("category", "")
    sizes = {name for name, _points in SIZE_LABELS.values()}
    return (
        size if size in sizes else "",
        category if category in CATEGORY_LABELS else "",
    )


@login_required()
def lucky_view(request):
    """ "Give me an issue": show a random free issue of the chosen size and
    category. It doesn't claim: the issue page (in the pop-up, via
    issue_modal.js) has the Claim button, and "Try another" comes back here
    with skip=<the one just shown>."""
    claims.release_expired()
    size, category = _lucky_filters(request)
    skip = request.GET.get("skip", "")
    issue = claims.random_free(size, category, int(skip) if skip.isdigit() else None)
    if issue is None:
        _claim_message(request, None, None, "none_free")
        return redirect("commits_issues")
    query = urlencode({"lucky": 1, "size": size, "category": category})
    return redirect(f"{reverse('commits_issue_detail', args=[issue.number])}?{query}")


def _open_claim_or_back(request, number):
    """(claim, None), or (None, a redirect with a message) when the issue
    isn't claimed or is closed. A closed issue's claim decides its points,
    so it's never released here; organisers use a credit override."""
    claim = Claim.objects.filter(issue_number=number).select_related("user").first()
    if claim is None:
        messages.info(
            request,
            _("#%(number)s isn't claimed any more.") % {"number": number},
            extra_tags="claim",
        )
        return None, _back(request)
    if not claims.is_open(claim):
        messages.warning(
            request,
            _(
                "#%(number)s is closed, so its claim stays: it decides who gets the "
                "points. To change that, add a credit override in /admin/."
            )
            % {"number": number},
            extra_tags="claim claim-limit",
        )
        return None, _back(request)
    return claim, None


@login_required()
@require_POST
def release_view(request, number):
    """The claimer lets go, or a helper force-releases (any time, also with
    an open PR or no time limit)."""
    claim, response = _open_claim_or_back(request, number)
    if response:
        return response
    mine = claim.user_id == request.user.pk
    if not mine and not can_see_solutions(request.user):
        raise PermissionDenied
    claim.delete()
    if mine:
        text = _("You released #%(number)s.") % {"number": number}
    else:
        text = _("Released #%(number)s from %(name)s. It's free to claim again.") % {
            "number": number,
            "name": claim.user.get_username(),
        }
    messages.success(request, text, extra_tags="claim claim-ok")
    return _back(request)


@login_required()
@require_POST
def keep_view(request, number):
    """The claimer's "Keep": the full time for the issue's size again."""
    claim, response = _open_claim_or_back(request, number)
    if response:
        return response
    if claim.user_id != request.user.pk:
        raise PermissionDenied
    issue = get_object_or_404(EventIssue, number=number)
    claims.keep(claim, issue)
    messages.success(
        request,
        _("#%(number)s is yours for %(minutes)s more minutes.")
        % {"number": number, "minutes": claims.default_minutes(issue)},
        extra_tags="claim claim-ok",
    )
    return _back(request)


@login_required()
@require_POST
def claim_time_view(request, number):
    """A helper changes one claim's time: plus15, plus30, unlimited or reset."""
    if not can_see_solutions(request.user):
        raise PermissionDenied
    action = request.POST.get("action", "")
    if action not in claims.ADJUST_ACTIONS:
        raise PermissionDenied
    claim, response = _open_claim_or_back(request, number)
    if response:
        return response
    issue = get_object_or_404(EventIssue, number=number)
    claims.adjust(claim, issue, action)
    left = claims.minutes_left(claim)
    messages.success(
        request,
        (
            _("#%(number)s now has no time limit.") % {"number": number}
            if left is None
            else _("#%(number)s now has %(minutes)s minutes left.")
            % {"number": number, "minutes": left}
        ),
        extra_tags="claim claim-ok",
    )
    return _back(request)
