"""Static legal/informational pages for account_app -- plain Django views
and templates rather than Wagtail Pages, since this is fixed text that
doesn't need CMS editing, not editorial content."""

from django.conf import settings
from django.shortcuts import render


def privacy_policy_view(request):
    """The site's privacy notice (GDPR Art. 13), including the content-
    ownership terms shown to new editors -- see account_settings_view's
    show_editor_notice, which links here (#editor-terms). retention_days is
    passed through rather than hardcoded in the template, so the two stay
    in sync if UNVERIFIED_ACCOUNT_RETENTION_DAYS is ever changed."""
    return render(
        request=request,
        template_name="legal/privacy_policy.html",
        context={"retention_days": settings.UNVERIFIED_ACCOUNT_RETENTION_DAYS},
    )
