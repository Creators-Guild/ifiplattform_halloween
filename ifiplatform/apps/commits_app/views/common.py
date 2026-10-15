"""Helpers the view modules share: what an issue card shows to this
visitor, where a button sends you back to, and the "Give me an issue"
filters."""

from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme

from commits_app import claims
from commits_app.labels import CATEGORY_LABELS, SIZE_LABELS
from commits_app.models import Claim, EventSolution, GitHubLink
from commits_app.permissions import can_see_solutions


def annotate(issues, user):
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
        issue.can_claim = bool(my_login) and claims.is_free(issue, claim is not None)
        issue.is_taken = is_open and (
            (claim is not None and not issue.is_mine)
            or (claim is None and bool(names) and my_login not in issue.assignees)
        )
    return issues


def back(request):
    """Back to the page the button was on (the list behind a pop-up, or an
    issue's own page), else the issue list."""
    referer = request.META.get("HTTP_REFERER", "")
    if url_has_allowed_host_and_scheme(
        referer, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(referer)
    return redirect("commits_issues")


def lucky_filters(request):
    """The size and category picked in "Give me an issue" ("" means any),
    ignoring anything that isn't a real one."""
    size = request.GET.get("size", "")
    category = request.GET.get("category", "")
    sizes = {name for name, _points in SIZE_LABELS.values()}
    return (
        size if size in sizes else "",
        category if category in CATEGORY_LABELS else "",
    )
