"""Whether a page's English copy is missing or out of date, seen from the nb
("OG") page -- what the editor-facing translation nudges run on.

Design rationale: docs/claude_context/translation_nudge.md"""

from django.db.models import Q
from django.urls import reverse
from wagtail.models import Locale, Page, Site
from wagtail_localize.machine_translators import get_machine_translator
from wagtail_localize.models import Translation

from .sync import SOURCE_LANGUAGE_CODE

TARGET_LANGUAGE_CODE = "en"


def _is_incomplete(translation):
    total, translated = translation.get_progress()
    return translated < total


def _get_translation(page):
    """The newest enabled wagtail-localize Translation of `page` into its own
    locale, or None (e.g. it was never submitted for translation)."""
    return (
        Translation.objects.filter(
            source__object_id=page.translation_key,
            target_locale_id=page.locale_id,
            enabled=True,
        )
        .order_by("-created_at")
        .first()
    )


def page_needs_translation(page):
    """True if `page` itself (a translated copy) is untranslated: still an
    untouched alias auto-created by locale synchronisation, or a real
    translation wagtail-localize considers incomplete. `alias_of` is
    unambiguous about which side of a locale pair is the placeholder."""
    if page.alias_of_id is not None:
        return True
    translation = _get_translation(page)
    return translation is not None and _is_incomplete(translation)


def _machine_url(nb_page, user):
    if user is None or not user.has_perm("wagtail_localize.submit_translation"):
        return None
    if get_machine_translator() is None:
        return None
    return reverse("machine_translate_page", args=[nb_page.id])


def _status(nb_page, en_page, user, reason):
    if reason == "missing":
        editor_url = reverse(
            "wagtail_localize:submit_page_translation", args=[nb_page.id]
        )
    else:
        editor_url = reverse("wagtailadmin_pages:edit", args=[en_page.id])
    return {
        "page": nb_page,
        "reason": reason,
        "editor_url": editor_url,
        "machine_url": _machine_url(nb_page, user),
    }


def _target_locale():
    return Locale.objects.filter(language_code=TARGET_LANGUAGE_CODE).first()


def translation_status(nb_page, user=None):
    """None if `nb_page` isn't an nb page or its English copy is up to date,
    else {"page", "reason" ("missing"/"outdated"), "editor_url", "machine_url"}."""
    if nb_page.is_root() or nb_page.locale.language_code != SOURCE_LANGUAGE_CODE:
        return None
    en_locale = _target_locale()
    if en_locale is None:
        return None
    en_page = nb_page.get_translation_or_none(en_locale)
    if en_page is None or en_page.alias_of_id is not None:
        return _status(nb_page, en_page, user, "missing")
    if page_needs_translation(en_page):
        return _status(nb_page, en_page, user, "outdated")
    return None


def pages_needing_translation(user=None, limit=25):
    """(total count, first `limit` statuses) for every nb page on a site
    whose English copy is missing or out of date, most recently published
    first. Batches the en-copy and Translation lookups; only the segment
    count is per page."""
    en_locale = _target_locale()
    site_roots = [site.root_page for site in Site.objects.select_related("root_page")]
    if en_locale is None or not site_roots:
        return 0, []
    on_a_site = Q()
    for root in site_roots:
        on_a_site |= Q(path__startswith=root.path)
    nb_pages = list(
        Page.objects.filter(
            on_a_site, locale__language_code=SOURCE_LANGUAGE_CODE
        ).order_by("-last_published_at")
    )
    en_by_key = {
        page.translation_key: page
        for page in Page.objects.filter(
            locale=en_locale, translation_key__in=[p.translation_key for p in nb_pages]
        )
    }
    translation_by_key = {}
    for translation in (
        Translation.objects.filter(
            target_locale=en_locale, enabled=True, source__object_id__in=list(en_by_key)
        )
        .select_related("source")
        .order_by("created_at")
    ):
        translation_by_key[translation.source.object_id] = translation

    statuses = []
    for nb_page in nb_pages:
        en_page = en_by_key.get(nb_page.translation_key)
        if en_page is None or en_page.alias_of_id is not None:
            statuses.append(_status(nb_page, en_page, user, "missing"))
            continue
        translation = translation_by_key.get(nb_page.translation_key)
        if translation is not None and _is_incomplete(translation):
            statuses.append(_status(nb_page, en_page, user, "outdated"))
    return len(statuses), statuses[:limit]
