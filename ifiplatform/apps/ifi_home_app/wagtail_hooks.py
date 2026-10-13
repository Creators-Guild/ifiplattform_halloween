"""Site-wide wagtail hooks for ifi_home_app.

The nb -> en synchronized-field auto-sync (see the function docstring below),
the "Machine-translate subtree"/"page" admin buttons/URLs (see
translation/views.py), the Norwegian-only admin (see
translation/admin_locales.py) and the translate-now nudges (see
translation/nudge.py) -- add
further hooks here rather than starting new files, unless a hook is
specific enough to a single feature area to warrant its own module."""

from django.dispatch import receiver
from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.widgets.button import Button
from wagtail.signals import page_published
from wagtail.snippets.models import register_snippet
from wagtail_localize.machine_translators import get_machine_translator

from .models import HeaderMessage, HomeBoardMessage, MenuGroup
from .translation import nudge
from .translation import views as translation_views
from .translation import admin_locales
from .translation.sync import SOURCE_LANGUAGE_CODE, sync_synchronized_fields


@hooks.register("register_admin_urls")
def register_admin_urls():
    return [
        path(
            "machine-translate-subtree/<int:page_id>/",
            translation_views.machine_translate_subtree,
            name="machine_translate_subtree",
        ),
        path(
            "machine-translate-page/<int:page_id>/",
            translation_views.machine_translate_page,
            name="machine_translate_page",
        ),
        path(
            "toggle-all-locales/",
            admin_locales.toggle_all_locales,
            name="toggle_all_locales",
        ),
    ]


hooks.register("construct_explorer_page_queryset", admin_locales.filter_explorer_pages)
hooks.register("construct_page_chooser_queryset", admin_locales.filter_chooser_pages)

# Translatable snippets -- registered here rather than with @register_snippet
# so their listing and chooser open on nb (see admin_locales.py).
for _snippet_model in (HeaderMessage, HomeBoardMessage, MenuGroup):
    register_snippet(_snippet_model, viewset=admin_locales.NorwegianFirstSnippetViewSet)


@hooks.register("register_admin_menu_item")
def register_toggle_all_locales_menu_item():
    return admin_locales.ToggleAllLocalesMenuItem()


hooks.register("after_publish_page", nudge.warn_after_publish)
hooks.register("before_edit_page", nudge.warn_on_edit)
hooks.register("construct_homepage_panels", nudge.add_dashboard_panel)
hooks.register("register_page_listing_buttons", nudge.listing_status_button)
hooks.register("register_page_header_buttons", nudge.machine_translate_button)
hooks.register("register_page_listing_more_buttons", nudge.machine_translate_button)


def _machine_translate_subtree_button(page, user, view_name=None, next_url=None):
    """Shown on nb pages with descendants -- see translation/views.py."""
    if (
        page.is_root()
        or page.locale.language_code != SOURCE_LANGUAGE_CODE
        or not page.get_descendants().exists()
        or not user.has_perm("wagtail_localize.submit_translation")
    ):
        return

    if get_machine_translator() is None:
        return

    yield Button(
        "Machine-translate subtree",
        reverse("machine_translate_subtree", args=[page.id]),
        priority=61,
        icon_name="doc-empty-inverse",
    )


hooks.register("register_page_header_buttons", _machine_translate_subtree_button)
hooks.register("register_page_listing_more_buttons", _machine_translate_subtree_button)


@receiver(page_published)
def sync_synchronized_fields_to_translations(sender, instance, revision, **kwargs):
    """On every nb page publish, push its wagtail-localize SynchronizedFields
    (status, etc.) out to every enabled translation, so they
    don't silently drift (see translation/sync.py).

    Listens on the page_published *signal* rather than Wagtail's
    after_publish_page *hook* -- that hook only fires from the single-page
    admin edit/create views, not from the page-listing bulk "Publish" action
    or from any script-based page.save_revision().publish() call (e.g.
    sync_peoply_events, seed_dev_data). page_published fires from
    Page.publish() itself, so it covers all of those uniformly. Safe against
    recursion: sync_synchronized_fields() publishes the *English* copy,
    which re-fires this same signal, but the locale guard below no-ops it
    immediately."""
    if instance.locale.language_code != SOURCE_LANGUAGE_CODE:
        return
    sync_synchronized_fields(instance, user=revision.user)
