"""Generic, content-agnostic helpers shared by every seeding mixin: page
get-or-create, storing English (translation/stored_translations.py), the
seed placeholder image and the default site root."""

from django.core.files.images import ImageFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils.text import slugify

from wagtail.coreutils import find_available_slug
from wagtail.images.models import Image
from wagtail.models import Page, Site
from wagtail.rich_text import RichText

from ifi_home_app.translation import english_urls, page_segments, stored_translations

from .constants import (
    ARTICLE_BODY,
    SAME_IN_ENGLISH,
    SEED_IMAGE_PATH,
    SEED_IMAGE_TITLE,
    TRANSLATIONS,
)

# The tables above are written as plain text, but pieces are stored escaped
# ("Paint &amp; Sip"), so look them up in that form too.
_STORED_TRANSLATIONS = {
    page_segments.stored_form(norwegian): page_segments.stored_form(english)
    for norwegian, english in TRANSLATIONS.items()
}
_STORED_SAME = {page_segments.stored_form(text) for text in SAME_IN_ENGLISH}


def _seed_english(stored_text):
    """English for one stored Norwegian piece, or None if the seed has none."""
    if stored_text in TRANSLATIONS:
        return TRANSLATIONS[stored_text]
    if stored_text in _STORED_TRANSLATIONS:
        return _STORED_TRANSLATIONS[stored_text]
    if stored_text in SAME_IN_ENGLISH or stored_text in _STORED_SAME:
        return stored_text
    return None


class SeedHelpersMixin:
    def _build_article_body(self, heading=None, text=None):
        if heading is None and text is None:
            return [item for item in ARTICLE_BODY]
        return [
            ("heading", {"text": heading, "level": "h2"}),
            ("paragraph", {"text": RichText(f"<p>{text}</p>")}),
        ]

    def _translate_page(self, obj):
        """Stores English for `obj` (a page or snippet) from TRANSLATIONS
        and SAME_IN_ENGLISH, as DeepL would; a page also gets its English
        slug from its English title. Text with no entry stays Norwegian.
        Re-runnable: English that's already stored is kept."""
        english = {}
        for segment in page_segments.extract_segments(obj):
            text = _seed_english(segment.norwegian_text)
            if text is not None:
                english[segment] = text
        if english:
            stored_translations.save_machine(obj, english)
        title = next(
            (text for segment, text in english.items() if segment.path == "title"),
            None,
        )
        if isinstance(obj, Page) and title and english_urls.english_slug(obj) is None:
            english_urls.set_english_slug(
                obj, page_segments.plain_text(title), "deepl", redirect=False
            )

    def _store_english(self, obj, english_by_field):
        """Stores English for plain text fields of `obj`, {field: English}."""
        english = {}
        for name, text in english_by_field.items():
            if text:
                for segment in page_segments.extract_segments(obj, name):
                    english[segment] = page_segments.stored_form(text)
        if english:
            stored_translations.save_machine(obj, english)

    # -- generic helpers ---------------------------------------------------

    def _get_or_create_page(
        self, parent, model, title, locale, slug=None, **field_kwargs
    ):
        slug = slug or slugify(title)
        existing = (
            model.objects.child_of(parent)
            .filter(slug=slug, locale_id=locale.id)
            .first()
        )
        if existing:
            self.skipped_count += 1
            return existing

        page = model(title=title, slug=slug, locale=locale, **field_kwargs)
        parent.add_child(instance=page)
        page.save_revision().publish()
        self.created_count += 1
        self.stdout.write(f"  created {model.__name__}: {title}")
        return page

    def _get_or_create_seed_image(self):
        existing = Image.objects.filter(title=SEED_IMAGE_TITLE).first()
        if existing:
            return existing

        if not SEED_IMAGE_PATH.exists():
            raise CommandError(f"Seed image not found at {SEED_IMAGE_PATH}")

        with open(SEED_IMAGE_PATH, "rb") as f:
            image = Image(
                title=SEED_IMAGE_TITLE,
                file=ImageFile(f, name=SEED_IMAGE_PATH.name),
            )
            image.save()
        return image

    def _set_default_site_root(self, root_page):
        site = Site.objects.filter(is_default_site=True).first()
        if site is None:
            Site.objects.get_or_create(
                hostname="localhost",
                defaults={
                    "port": 80,
                    "root_page": root_page,
                    "is_default_site": True,
                },
            )
        elif site.root_page_id != root_page.id:
            site.root_page = root_page
            site.save()
