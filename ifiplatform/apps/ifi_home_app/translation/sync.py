"""Push of wagtail-localize "synchronized fields" (status, and
anything else get_translatable_fields() classifies as SynchronizedField --
see wagtail_localize/fields.py) from an nb/"OG" page to its existing
translations. Shared by:
- wagtail_hooks.sync_synchronized_fields_to_translations (automatic, on
  every nb page publish through wagtail-admin)
- views/article_views.sync_mirrored_page (the manual "Sync mirrored page"
  editor-mode button)
- views/article_views.publish_page (ArticlePage's own editor-mode Publish
  button, which bypasses wagtail-admin entirely and so never fires the hook
  above)
- management/commands/sync_translated_page_fields.py (one-off catch-up for
  pages that drifted before any of this existed)

One shared implementation rather than four copies -- duplicating "how do we
resync a translation" is exactly the kind of drift this module exists to
prevent."""

from django.core.exceptions import ValidationError
from wagtail_localize.models import TranslationSource

SOURCE_LANGUAGE_CODE = "nb"  # the anchor/"OG" locale every other locale
# mirrors -- matches ArticlePage.SOURCE_LANGUAGE_CODE


def sync_synchronized_fields(page, user=None):
    """Push `page`'s wagtail-localize SynchronizedFields out to every one of
    its enabled translations. `page` must already be the nb/"OG" copy --
    callers are responsible for that check (EditorModeMixin.
    can_sync_mirrored_page and the wagtail hook's own locale guard both do
    it before this ever runs).

    Returns the list of target Locales actually synced (empty if there's no
    TranslationSource yet, i.e. the page was never submitted for
    translation -- not an error, just nothing to do)."""
    source = TranslationSource.objects.get_for_instance_or_none(page)
    if source is None:
        return []

    # save_target() re-applies synchronized fields from this source's stored
    # content_json snapshot, not the live DB row -- refresh it first, same as
    # wagtail_localize's own UpdateTranslationsView.form_valid does before
    # calling save_target().
    source.update_from_db()
    synced_locales = []
    for translation in source.translations.filter(enabled=True):
        try:
            translation.save_target(user=user, publish=True)
            synced_locales.append(translation.target_locale)
        except ValidationError:
            continue
    return synced_locales
