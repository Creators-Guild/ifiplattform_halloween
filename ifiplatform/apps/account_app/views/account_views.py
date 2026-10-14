"""Views for account settings and user profile management."""

import json

from django.conf import settings
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core import signing
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST

from account_app.forms import AccountDeleteForm, NicknameForm, ProfileForm
from account_app.models import Profile
from account_app.permissions import is_pending_editor
from ifi_home_app.models import ArticlePage
from study_app.models import Card, Deck

_EMAIL_CHANGE_SALT = "account_app.email_change"
_EMAIL_CHANGE_MAX_AGE = 60 * 60 * 24 * 3  # 3 days

# Groups granting editor rights are found via GroupPagePermission's own
# 'add'/'change' codenames on Page -- same actions is_pending_editor (see
# account_app.permissions) treats as "can write pages".
_PAGE_EDIT_CODENAMES = ["add_page", "change_page"]


def _send_email_change_confirmation(request, user, new_email):
    """Email `new_email` a link to confirm it before it actually replaces
    user.email -- otherwise "changing" your email would just be typing in
    any address you don't have to prove you own, same gap the original
    signup flow closed with a verification link."""
    token = signing.dumps(
        {"user_id": user.pk, "new_email": new_email}, salt=_EMAIL_CHANGE_SALT
    )
    confirm_url = request.build_absolute_uri(
        reverse("confirm_email_change", kwargs={"token": token})
    )
    message = render_to_string(
        "login/email/email_change_confirmation.txt",
        {"user": user, "new_email": new_email, "confirm_url": confirm_url},
    )
    send_mail(
        subject="Confirm your new Ifi Platform email",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[new_email],
    )
    if settings.DEBUG:
        print(f"[email change confirmation] {new_email} -> {confirm_url}")


def _account_settings_context(request, *, form=None, delete_form=None):
    """Shared context for core/account_settings.html -- used both by a
    normal GET/POST render (account_settings_view) and by delete_account_view
    re-rendering the same page with AccountDeleteForm's own validation
    errors on it, so the two don't duplicate the profile_incomplete/editor-
    notice computation."""
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)
    allow_clearing = user.is_staff or user.is_superuser

    profile_incomplete = not (user.email and user.first_name and user.last_name)
    show_editor_notice = is_pending_editor(user)

    return {
        "user": user,
        "form": form or ProfileForm(instance=user, allow_clearing=allow_clearing),
        "profile_incomplete": profile_incomplete,
        "pending_email": profile.pending_email,
        "nickname_form": NicknameForm(instance=profile),
        "delete_form": delete_form or AccountDeleteForm(user=user),
        "show_editor_notice": show_editor_notice,
        "editor_terms_just_disagreed": request.GET.get("editor_terms") == "disagreed",
        # set only by EditorTermsGateMiddleware's redirect -- shakes the
        # terms box on that "caught mid-attempt" landing, not on a plain
        # self-navigated visit to this page (which carries no query param).
        "editor_terms_shake": request.GET.get("editor_terms") == "required",
    }


@login_required()
def account_settings_view(request):
    """Render the account settings page for the currently logged-in user,
    with an editable (optional) profile form -- see ProfileForm. Name
    changes apply immediately; an email change is held back until the new
    address is confirmed (see _send_email_change_confirmation), tracked via
    profile.pending_email so this page can show/cancel it in the meantime."""
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)
    allow_clearing = user.is_staff or user.is_superuser
    if request.method == "POST":
        # ModelForm.is_valid() mutates the bound instance in place (via
        # _post_clean() -> construct_instance()) before this view ever runs
        # -- capture the pre-change value now, or comparing user.email to
        # the submitted value below would always see them as equal.
        original_email = user.email
        form = ProfileForm(request.POST, instance=user, allow_clearing=allow_clearing)
        if form.is_valid():
            new_email = form.cleaned_data["email"]
            email_changed = new_email != (original_email or "")

            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]

            if email_changed and new_email:
                # construct_instance() (above, inside is_valid()) already
                # wrote new_email onto user.email in memory -- put the old
                # one back before saving, so only the name changes persist
                # and the address on file doesn't change until confirmed.
                user.email = original_email
                user.save()
                profile.pending_email = new_email
                profile.save(update_fields=["pending_email"])
                _send_email_change_confirmation(request, user, new_email)
                return redirect("email_change_sent")

            # unchanged, or an admin clearing it to blank (allow_clearing) --
            # nothing to confirm either way, apply directly. Also clears any
            # unrelated pending change still sitting around from earlier.
            user.email = new_email
            user.save()
            if profile.pending_email:
                profile.pending_email = ""
                profile.save(update_fields=["pending_email"])
            return redirect("account_settings")
    else:
        form = ProfileForm(instance=user, allow_clearing=allow_clearing)

    return render(
        request=request,
        template_name="core/account_settings.html",
        context=_account_settings_context(request, form=form),
    )


@login_required()
@require_POST
def update_nickname_view(request):
    """Set/change the nickname on the current user's Profile -- see
    NicknameForm."""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = NicknameForm(request.POST, instance=profile)
    if form.is_valid():
        form.save()
    return redirect("account_settings")


@login_required()
@require_POST
def editor_terms_response_view(request):
    """Records the current user's response to the content-ownership terms
    shown once they're granted permission to write pages (see
    account_settings_view's show_editor_notice). Agreeing just records the
    decision; disagreeing also revokes the permission itself -- only the
    specific group(s) actually granting add/change page rights, leaving any
    other, unrelated group membership untouched."""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    decision = request.POST.get("decision")

    if decision == "agree":
        profile.editor_terms_status = "agreed"
        profile.save(update_fields=["editor_terms_status"])
        return redirect("account_settings")

    if decision == "disagree":
        profile.editor_terms_status = "disagreed"
        profile.save(update_fields=["editor_terms_status"])
        editor_groups = Group.objects.filter(
            user=request.user,
            page_permissions__permission__codename__in=_PAGE_EDIT_CODENAMES,
        ).distinct()
        request.user.groups.remove(*editor_groups)
        return redirect(reverse("account_settings") + "?editor_terms=disagreed")

    return redirect("account_settings")


@login_required()
def export_data_view(request):
    """Lets a user download the personal data IfiPlatform holds on them
    (GDPR Art. 15/20) as a JSON file: account fields, owned study decks/
    cards, and authored articles."""
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    data = {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "nickname": profile.nickname,
        "date_joined": user.date_joined.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "decks": [
            {
                "name": deck.name,
                "description": deck.description,
                "cards": [
                    {
                        "front": card.front,
                        "back": card.back,
                        "created_at": card.created_at.isoformat(),
                    }
                    for card in deck.cards.all()
                ],
            }
            for deck in user.decks.all()
        ],
        "authored_articles": [
            {
                "title": article.title,
                "slug": article.slug,
                "published_date": (
                    article.published_date.isoformat()
                    if article.published_date
                    else None
                ),
                "author_attribution": article.author_attribution,
            }
            for article in ArticlePage.objects.filter(author=user)
        ],
    }

    response = HttpResponse(
        json.dumps(data, indent=2, ensure_ascii=False), content_type="application/json"
    )
    response["Content-Disposition"] = 'attachment; filename="ifiplatform_my_data.json"'
    return response


@login_required()
@require_POST
def delete_account_view(request):
    """Self-service account deletion (GDPR Art. 17) -- see AccountDeleteForm
    for the password re-auth + study-tools/articles choices this reads.
    Everything that needs the still-live user/profile/FKs happens before
    user.delete() itself; Profile cascades away with it, and Deck.owner/
    ArticlePage.author (for anything not already explicitly deleted below)
    become NULL automatically via their existing on_delete=SET_NULL."""
    user = request.user
    form = AccountDeleteForm(request.POST, user=user)
    if not form.is_valid():
        context = _account_settings_context(request, delete_form=form)
        context["delete_form_open"] = True
        return render(
            request=request, template_name="core/account_settings.html", context=context
        )

    profile, _ = Profile.objects.get_or_create(user=user)
    real_name = user.get_full_name() or user.username
    nickname = profile.nickname

    def _resolve(choice):
        return {"real_name": real_name, "nickname": nickname, "unknown": "unknown"}[
            choice
        ]

    if form.cleaned_data["study_tools_action"] == "delete":
        Card.objects.filter(deck__owner=user).delete()
        Deck.objects.filter(owner=user).delete()
    else:
        resolved = _resolve(form.cleaned_data["study_tools_attribution"])
        Deck.objects.filter(owner=user).update(owner_display_name=resolved)

    resolved_articles = _resolve(form.cleaned_data["articles_attribution"])
    ArticlePage.objects.filter(author=user).update(
        author_display_name=resolved_articles
    )

    user.delete()
    logout(request)

    return render(request=request, template_name="login/account_deleted.html")


@login_required()
def cancel_email_change_view(request):
    """Drop a pending email change, leaving the current (old) address in
    place -- only meaningful while it's still unconfirmed."""
    if request.method == "POST":
        Profile.objects.filter(user=request.user).update(pending_email="")
    return redirect("account_settings")


def email_change_sent_view(request):
    """Shown after requesting an email change, telling the user to check
    the *new* address for a confirmation link."""
    return render(request=request, template_name="login/email_change_sent.html")


def confirm_email_change_view(request, token):
    """Apply a pending email change once the new address confirms it."""
    try:
        data = signing.loads(
            token, salt=_EMAIL_CHANGE_SALT, max_age=_EMAIL_CHANGE_MAX_AGE
        )
    except signing.BadSignature:
        return render(request=request, template_name="login/email_change_invalid.html")

    User = get_user_model()
    try:
        user = User.objects.get(pk=data["user_id"])
    except User.DoesNotExist:
        return render(request=request, template_name="login/email_change_invalid.html")

    new_email = data["new_email"]
    profile, _ = Profile.objects.get_or_create(user=user)
    # profile.pending_email won't match if the change was cancelled, or a
    # newer/different change was requested since this link was sent -- the
    # token alone can't tell either of those apart, so re-check here.
    if profile.pending_email != new_email:
        return render(request=request, template_name="login/email_change_invalid.html")

    # re-check uniqueness -- someone else could have taken it in the days
    # since this link was sent (the token itself has no idea).
    if User.objects.filter(email__iexact=new_email).exclude(pk=user.pk).exists():
        return render(request=request, template_name="login/email_change_invalid.html")

    user.email = new_email
    user.save(update_fields=["email"])
    profile.pending_email = ""
    profile.save(update_fields=["pending_email"])
    return render(
        request=request,
        template_name="login/email_change_success.html",
        context={"user": user},
    )
