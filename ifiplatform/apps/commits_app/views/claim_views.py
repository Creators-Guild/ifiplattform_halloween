"""The claim buttons: Claim, "Give me an issue", Keep, Release, and the
helpers' time buttons. The rules are in claims.py; these views turn its
answers into messages and send the visitor back to the page they were on."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from commits_app import claims
from commits_app.models import Claim, EventIssue
from commits_app.permissions import can_see_solutions

from .common import back, lucky_filters


def _claim_message(request, issue, reason):
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
    _new, reason = claims.claim(request.user, issue)
    _claim_message(request, issue, reason)
    return back(request)


@login_required()
def lucky_view(request):
    """ "Give me an issue": show a random free issue of the chosen size and
    category. It doesn't claim: the issue page (in the pop-up, via
    issue_modal.js) has the Claim button, and "Try another" comes back here
    with skip=<the one just shown>."""
    claims.release_expired()
    size, category = lucky_filters(request)
    skip = request.GET.get("skip", "")
    issue = claims.random_free(size, category, int(skip) if skip.isdecimal() else None)
    if issue is None:
        _claim_message(request, None, "none_free")
        return redirect("commits_issues")
    query = urlencode({"lucky": 1, "size": size, "category": category})
    return redirect(f"{reverse('commits_issue_detail', args=[issue.number])}?{query}")


def _gone(request, number):
    """Back, saying the claim has been released (it ran out, or the claimer
    or a helper let it go) since the page was loaded."""
    messages.info(
        request,
        _("#%(number)s isn't claimed any more.") % {"number": number},
        extra_tags="claim",
    )
    return back(request)


def _open_claim_or_back(request, number):
    """(claim, None), or (None, a redirect with a message) when the issue
    isn't claimed or is closed. A closed issue's claim decides its points,
    so it's never released here; organisers use a credit override."""
    claim = Claim.objects.filter(issue_number=number).select_related("user").first()
    if claim is None:
        return None, _gone(request, number)
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
        return None, back(request)
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
    return back(request)


@login_required()
@require_POST
def keep_view(request, number):
    """The claimer's "Keep": the full time for the issue's size again. A
    claim that already ran out is released first, not brought back."""
    claims.release_expired()
    claim, response = _open_claim_or_back(request, number)
    if response:
        return response
    if claim.user_id != request.user.pk:
        raise PermissionDenied
    issue = get_object_or_404(EventIssue, number=number)
    if not claims.keep(claim, issue):
        return _gone(request, number)
    messages.success(
        request,
        _("#%(number)s is yours for %(minutes)s more minutes.")
        % {"number": number, "minutes": claims.default_minutes(issue)},
        extra_tags="claim claim-ok",
    )
    return back(request)


@login_required()
@require_POST
def claim_time_view(request, number):
    """A helper changes one claim's time: plus15, plus30, unlimited or reset."""
    if not can_see_solutions(request.user):
        raise PermissionDenied
    action = request.POST.get("action", "")
    if action not in claims.ADJUST_ACTIONS:
        raise PermissionDenied
    claims.release_expired()
    claim, response = _open_claim_or_back(request, number)
    if response:
        return response
    issue = get_object_or_404(EventIssue, number=number)
    if not claims.adjust(claim, issue, action):
        return _gone(request, number)
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
    return back(request)
