"""wagtail-admin views for machine-translating an nb page -- or its entire
subtree -- into English in one action, from one confirm screen.

Design rationale/history: docs/claude_context/translation_views.md"""

import shutil
import subprocess
import sys

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from wagtail.models import Page

from wagtail_localize.machine_translators import get_machine_translator

from .sync import SOURCE_LANGUAGE_CODE

# The only other locale this bilingual site has -- see sync.py's own
# SOURCE_LANGUAGE_CODE comment for why nb is the anchor.
TARGET_LANGUAGE_CODE = "en"

# journalctl -t <this> -f shows progress -- see machine_translate_subtree
# management command (the actual implementation, run as a background
# process by this view) and docs/claude_context/translation_views.md.
JOURNAL_TAG = "machine-translate-subtree"


@login_required
@require_http_methods(["GET", "POST"])
def machine_translate_subtree(request, page_id):
    """GET shows a confirm screen (page + descendant count); POST launches
    the actual translation as a detached background process (see
    machine_translate_subtree management command) and redirects back to
    the page's edit view immediately -- a real subtree is too slow for any
    request/response cycle, see docs/claude_context/translation_views.md."""
    return _machine_translate(request, page_id, page_only=False)


@login_required
@require_http_methods(["GET", "POST"])
def machine_translate_page(request, page_id):
    """Same as machine_translate_subtree, for just this one page -- the
    "Machine-translate now" button of the translation nudges
    (docs/claude_context/translation_nudge.md)."""
    return _machine_translate(request, page_id, page_only=True)


def _machine_translate(request, page_id, page_only):
    if not request.user.has_perms(["wagtail_localize.submit_translation"]):
        raise PermissionDenied

    page = get_object_or_404(Page, id=page_id).specific
    if page.locale.language_code != SOURCE_LANGUAGE_CODE:
        raise PermissionDenied(
            f"Only pages in the anchor locale ({SOURCE_LANGUAGE_CODE}) can be "
            "mass machine-translated."
        )

    machine_translator = get_machine_translator()
    if machine_translator is None:
        messages.error(request, "No machine translator is configured.")
        return redirect(reverse("wagtailadmin_pages:edit", args=[page.id]))

    pages = [page] if page_only else [page, *page.get_descendants()]

    if request.method == "POST":
        if "dry_run" in request.POST:
            # No TranslationCreator, no machine_translator call, no DB
            # writes -- just reports the same page list the background
            # command would act on, so you can sanity-check scope (and
            # avoid burning DeepL quota on a subtree that's bigger than
            # intended) before actually committing to it.
            titles = [str(p) for p in pages]
            shown = ", ".join(titles[:10])
            if len(titles) > 10:
                shown += f", and {len(titles) - 10} more"
            messages.info(
                request,
                f"Dry run: would machine-translate and publish {len(pages)} page(s) -- {shown}",
            )
            return redirect(reverse("wagtailadmin_pages:edit", args=[page.id]))

        # start_new_session=True detaches the child into its own session,
        # so it survives independently of gunicorn's process group -- a
        # plain background thread would die the moment this worker gets
        # recycled or the service restarts (e.g. the next deploy), silently
        # losing all in-progress translation. On the real server, systemd-cat
        # routes its stdout/stderr into the journal under JOURNAL_TAG, since
        # it's no longer a gunicorn child and so no longer shows up under
        # `journalctl -u gunicorn`. systemd-cat doesn't exist on local dev
        # (e.g. Windows) -- fall back to plain inheritance there, so
        # progress still shows up directly in the runserver terminal.
        base_command = [
            sys.executable,
            "manage.py",
            "machine_translate_subtree",
            str(page.id),
            str(request.user.id),
            *(["--page-only"] if page_only else []),
        ]
        systemd_cat = shutil.which("systemd-cat")
        if systemd_cat:
            subprocess.Popen(
                [systemd_cat, "-t", JOURNAL_TAG, *base_command],
                cwd=settings.BASE_DIR,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            progress_hint = f"check progress with journalctl -t {JOURNAL_TAG}"
        else:
            subprocess.Popen(
                base_command,
                cwd=settings.BASE_DIR,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
            progress_hint = "check the runserver terminal for progress"
        messages.success(
            request,
            f"Started machine-translating {len(pages)} page(s) in the background -- "
            f"{progress_hint}.",
        )
        return redirect(reverse("wagtailadmin_pages:edit", args=[page.id]))

    return render(
        request,
        "translation/machine_translate_subtree_confirm.html",
        {"page": page, "descendant_count": len(pages) - 1, "page_only": page_only},
    )
