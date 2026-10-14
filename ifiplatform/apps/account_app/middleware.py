"""Gates access to Wagtail admin on the editor content-ownership terms --
see account_app.permissions.is_pending_editor for what "pending" means.

Without this, a user granted page-add/change permission (e.g. added to
Wagtail's built-in "Editors" group via Django admin) could go straight into
/wagtail-admin/ and start editing without ever seeing/answering the notice
account_settings_view shows -- that notice is only rendered on the Account
Settings page itself, so nothing stopped a pending editor from simply never
visiting it. This middleware is what actually enforces "must respond before
continuing", by intercepting the one place that permission is ever put to
use."""

from django.shortcuts import redirect
from django.urls import reverse

from account_app.permissions import is_pending_editor

# wagtail-admin/ is mounted inside i18n_patterns (see ifiplatform_project/
# urls.py), so the real request path is locale-prefixed (/en/wagtail-admin/,
# /nb/wagtail-admin/) -- matched as a substring rather than a fixed prefix.
_WAGTAIL_ADMIN_PATH_MARKER = "/wagtail-admin/"


class EditorTermsGateMiddleware:
    """Redirects a pending editor's request to /wagtail-admin/ (any path
    under it) to account_settings instead, where the notice they still need
    to respond to is shown. Everyone else (anonymous users, admins,
    non-editors, editors who already agreed) passes through untouched."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if _WAGTAIL_ADMIN_PATH_MARKER in request.path and is_pending_editor(
            request.user
        ):
            # ?editor_terms=required -- read by _account_settings_context to
            # shake the terms box, but only for this "caught mid-attempt"
            # landing, not a plain self-navigated visit to the page.
            return redirect(reverse("account_settings") + "?editor_terms=required")
        return self.get_response(request)
