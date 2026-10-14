"""Site-wide wagtail hooks for ifi_home_app.

The English editor (its URL, the "English" buttons on pages and snippets,
the read-only "Stored English" list -- see translation/english_editor.py),
the translate-now nudges (see translation/nudge.py), the translated
snippets' registration, and hiding what's left of wagtail-localize's admin
-- add further hooks here rather than starting new files, unless a hook is
specific enough to a single feature area to warrant its own module."""

from django.templatetags.static import static
from django.urls import path
from django.utils.html import format_html
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.ui.sidebar import LinkMenuItem
from wagtail.snippets.models import register_snippet

from .models import HeaderMessage, HomeBoardMessage, MenuGroup
from . import admin_dashboard
from .translation import english_editor, nudge


@hooks.register("register_admin_urls")
def register_admin_urls():
    return [
        path(
            "english/<int:content_type_id>/<int:object_id>/",
            english_editor.edit,
            name="english_editor",
        ),
        path(
            "english/subtree/<int:page_id>/",
            english_editor.machine_translate_subtree,
            name="english_machine_translate_subtree",
        ),
        path(
            "english/menu/<int:menu_id>/",
            english_editor.machine_translate_menu,
            name="english_machine_translate_menu",
        ),
    ]


@hooks.register("register_admin_viewset")
def register_stored_english_viewset():
    return english_editor.StoredEnglishViewSet("stored_english")


hooks.register("register_page_header_buttons", english_editor.page_button)
hooks.register("register_page_listing_more_buttons", english_editor.page_button)
hooks.register("register_page_header_buttons", english_editor.subtree_button)
hooks.register("register_page_listing_more_buttons", english_editor.subtree_button)
hooks.register("register_snippet_listing_buttons", english_editor.snippet_button)

for _snippet_model in (HeaderMessage, HomeBoardMessage, MenuGroup):
    register_snippet(_snippet_model)

hooks.register("after_publish_page", nudge.warn_after_publish)
hooks.register("before_edit_page", nudge.warn_on_edit)
hooks.register("construct_homepage_panels", admin_dashboard.add_dashboard_panel)


class LanguageSwitchMenuItem(MenuItem):
    """Sidebar link to the same admin page in the other language. The admin
    speaks the language of its address (/nb/ or /en/) unless a user picked
    one in Account -> Preferences."""

    OTHER = {"nb": ("en", "English"), "en": ("nb", "Norsk")}

    def _target(self, request):
        language = request.path.split("/")[1]
        if language not in self.OTHER:
            return None
        other, label = self.OTHER[language]
        return label, f"/{other}" + request.get_full_path()[len(language) + 1 :]

    def is_shown(self, request):
        return self._target(request) is not None

    def render_component(self, request):
        label, url = self._target(request)
        return LinkMenuItem(self.name, label, url, icon_name=self.icon_name)


@hooks.register("register_admin_menu_item")
def register_language_switch():
    return LanguageSwitchMenuItem(
        "Language", "", name="language", icon_name="site", order=10500
    )


@hooks.register("insert_global_admin_css")
def dashboard_panel_css():
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static("css/06_components/admin/dashboard_panel.css"),
    )


hooks.register("construct_homepage_panels", nudge.add_dashboard_panel)
hooks.register("register_page_listing_buttons", nudge.listing_status_button)


@hooks.register("construct_reports_menu")
def hide_wagtail_localize_report(request, menu_items):
    """wagtail-localize stays installed only for translation/page_segments.py;
    its "Translations" report has nothing to show. Its other buttons hide
    themselves: they need a second locale or translation records, and the
    switch-over removed both."""
    menu_items[:] = [item for item in menu_items if item.name != "translations"]
