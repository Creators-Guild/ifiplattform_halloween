"""Register an already-existing translated snippet copy with wagtail-localize,
so it's mirrored from its nb source (translation editor + sync) instead of
being an unlinked copy. Keeps the copy's current text as the translation.

Design rationale: docs/claude_context/menus.md"""

from wagtail_localize.models import Translation, TranslationSource


def _value_at(obj, path):
    """The target object's current text at a segment path such as "title"
    or "links.<translation_key>.label" (a TranslatableMixin child, matched
    by its shared translation_key)."""
    parts = path.split(".")
    if len(parts) == 1:
        return getattr(obj, parts[0], "")
    relation, translation_key, field = parts
    child = next(
        (
            c
            for c in getattr(obj, relation).all()
            if str(c.translation_key) == translation_key
        ),
        None,
    )
    return getattr(child, field, "") if child else ""


def link_existing_translation(source_obj, target_obj):
    """Returns the Translation, creating it (and its strings) only if it
    didn't exist yet -- safe to call repeatedly."""
    source, _ = TranslationSource.get_or_create_from_instance(source_obj)
    translation, created = Translation.objects.get_or_create(
        source=source, target_locale=target_obj.locale
    )
    if not created:
        return translation

    po = translation.export_po()
    for entry in po:
        entry.msgstr = _value_at(target_obj, entry.msgctxt) or entry.msgid
    translation.import_po(po, tool_name="link_existing_translation")
    translation.save_target()
    return translation
