"""Editor-facing nudges to translate a page right away, now that English is
hidden in the admin: a warning message after publishing and on the edit
view, a dashboard panel, and a "Needs translation" button in the explorer.
All run on translation_status() (status.py).

Design rationale: docs/claude_context/translation_nudge.md"""

from wagtail.admin import messages
from wagtail.admin.ui.components import Component
from wagtail.admin.widgets import ListingButton

from .status import pages_needing_translation, translation_status

REASON_TEXT = {
    "missing": "The English version of this page is missing.",
    "outdated": "The English version of this page is out of date.",
}


def warn(request, page):
    """Adds the translate-now warning message for `page`, if it needs one."""
    status = translation_status(page, request.user)
    if status is None:
        return
    buttons = [messages.button(status["editor_url"], "Open translation editor")]
    if status["machine_url"]:
        buttons.insert(
            0, messages.button(status["machine_url"], "Machine-translate now")
        )
    messages.warning(request, REASON_TEXT[status["reason"]], buttons=buttons)


def warn_after_publish(request, page):
    warn(request, page)


def warn_on_edit(request, page):
    if request.method == "GET":
        warn(request, page)


def listing_status_button(page, user, next_url=None):
    status = translation_status(page, user)
    if status is not None:
        yield ListingButton(
            "Needs translation",
            status["editor_url"],
            icon_name="warning",
            priority=5,
            attrs={"title": REASON_TEXT[status["reason"]]},
        )


def machine_translate_button(page, user, view_name=None, next_url=None):
    status = translation_status(page, user)
    if status is not None and status["machine_url"]:
        yield ListingButton(
            "Machine-translate now",
            status["machine_url"],
            icon_name="doc-empty-inverse",
            priority=59,
        )


class TranslationsNeededPanel(Component):
    name = "translations_needed"
    order = 50
    template_name = "wagtailadmin/home/translations_needed.html"

    def __init__(self, user):
        self.total, self.statuses = pages_needing_translation(user)

    def render_html(self, parent_context=None):
        if not self.total:
            return ""
        return super().render_html(parent_context)

    def get_context_data(self, parent_context=None):
        return {
            "heading": f"Needs English translation ({self.total})",
            "total": self.total,
            "statuses": self.statuses,
        }


def add_dashboard_panel(request, panels):
    panels.append(TranslationsNeededPanel(request.user))
