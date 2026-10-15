"""Views for the event points system's pages: My issues (link your GitHub
username, see your issues and points), the leaderboard with its organiser
buttons, Sync now, and an issue's own page (also shown in the pop-up, with
the helpers' solution). The issue board is in board_views.py and the claim
buttons in claim_views.py. The leaderboard and the issues are public; My
issues and the organiser buttons are not."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from commits_app import claims
from commits_app.forms import GitHubLinkForm
from commits_app.github_sync import maybe_sync, sync
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

from .common import annotate, back, lucky_filters


@login_required()
def main_view(request):
    """The Commits page: link your GitHub username, see your points and drink progress."""
    link = GitHubLink.objects.filter(user=request.user).first()
    if request.method == "POST":
        form = GitHubLinkForm(request.POST, user=request.user)
        if form.is_valid() and form.save():
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
        open_issues = annotate(
            list(EventIssue.objects.exclude(state="CLOSED").select_related("credit")),
            request.user,
        )
        # Claimed here or assigned on GitHub: both are yours.
        mine = [i for i in open_issues if i.is_mine or link.github_login in i.assignees]
        annotate(score.issues, request.user)
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
    return back(request)


def issue_detail_view(request, number):
    claims.release_expired()
    issue = get_object_or_404(
        EventIssue.objects.select_related("credit"), number=number
    )
    show_solutions = can_see_solutions(request.user)
    annotate([issue], request.user)
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
                        zip(("size", "category"), lucky_filters(request)),
                        skip=number,
                    )
                )
                if request.GET.get("lucky")
                else ""
            ),
            "sub_issues": annotate(
                list(EventIssue.objects.filter(parent_number=number)), request.user
            ),
            "solution": (
                EventSolution.objects.filter(issue_number=number).first()
                if show_solutions
                else None
            ),
        },
    )
