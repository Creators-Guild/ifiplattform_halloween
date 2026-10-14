"""Editor-facing nudges when a page's English is missing or out of date and
DeepL isn't on its way: a warning message after publishing and on the edit
view, a dashboard panel, and a "Needs translation" button in the explorer,
each linking to the English editor. All run on status.py.

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
    buttons = [messages.button(status["editor_url"], "Open English editor")]
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


class TranslationsNeededPanel(Component):
    name = "translations_needed"
    order = 50
    template_name = "wagtailadmin/home/translations_needed.html"

    def __init__(self, user):
        self.total, self.statuses = pages_needing_translation(user)

    def get_context_data(self, parent_context=None):
        return {
            "heading": (
                f"Needs English translation ({self.total})"
                if self.total
                else "English translation"
            ),
            "total": self.total,
            "statuses": self.statuses,
        }


def add_dashboard_panel(request, panels):
    panels.append(TranslationsNeededPanel(request.user))
