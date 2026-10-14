"""Shared editor-permission checks -- used both by account_settings_view
(to decide whether to show the content-ownership notice) and
EditorTermsGateMiddleware (to actually gate wagtail-admin access on it),
so the two can't drift out of sync on what counts as "a pending editor"."""

from wagtail.permissions import page_permission_policy

from account_app.models import Profile


def is_pending_editor(user):
    """True if `user` currently holds permission to add/change pages, isn't
    exempt as an admin (staff/superuser -- see PagePermissionPolicy's own
    unconditional True for superusers, which is exactly why is_admin must be
    checked first and short-circuit before ever calling into it), and hasn't
    agreed to the content-ownership terms (see Profile.editor_terms_status).
    False for anonymous users, admins, and non-editors. Also false for
    editors who already agreed -- but not simply for status=="pending":
    checking "!= agreed" instead means that if staff ever re-grant page
    permission to someone who'd previously disagreed (editor_terms_status
    stays "disagreed" -- see editor_terms_response_view, which only ever
    revokes the permission, never resets the status), this goes back to
    True and the terms are shown again, with no separate plumbing needed to
    reset that status back to "pending" first. A disagreed user whose
    permission was never re-granted still fails the permission check above
    regardless."""
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return False
    if not page_permission_policy.user_has_any_permission(user, {"add", "change"}):
        return False
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile.editor_terms_status != "agreed"
