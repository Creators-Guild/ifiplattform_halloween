"""Generic, content-agnostic helpers shared by every seeding mixin: page
get-or-create, the wagtail_localize PO-pipeline translation helper, the
seed placeholder image, default site root, and English locale sync."""

from django.core.files.images import ImageFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils.text import slugify

from wagtail.coreutils import find_available_slug
from wagtail.images.models import Image
from wagtail.models import Site
from wagtail.rich_text import RichText
from wagtail_localize.models import (
    LocaleSynchronization,
    Translation,
    TranslationSource,
)

from .constants import ARTICLE_BODY, SEED_IMAGE_PATH, SEED_IMAGE_TITLE, TRANSLATIONS


class SeedHelpersMixin:
    def _build_article_body(self, heading=None, text=None):
        if heading is None and text is None:
            return [item for item in ARTICLE_BODY]
        return [
            ("heading", {"text": heading, "level": "h2"}),
            ("paragraph", {"text": RichText(f"<p>{text}</p>")}),
        ]

    def _translate_page(self, nb_page, en_locale):
        """Produce a real English translation of `nb_page` via wagtail_localize's
        actual PO import/export pipeline (submit for translation -> export PO ->
        fill in msgstr from TRANSLATIONS -> import PO -> publish), rather than
        hand-writing a second copy of every field. Strings with no entry in
        TRANSLATIONS are left untranslated and fall back to the nb text."""
        if nb_page.has_translation(en_locale):
            self.skipped_count += 1
            return nb_page.get_translation(en_locale)

        source, _ = TranslationSource.get_or_create_from_instance(nb_page)
        translation, _ = Translation.objects.get_or_create(
            source=source, target_locale=en_locale
        )

        po = translation.export_po()
        for entry in po:
            text = TRANSLATIONS.get(entry.msgid)
            if text:
                entry.msgstr = text
        translation.import_po(po, translation_type="machine", tool_name="Seed script")
        translation.save_target(publish=True)

        # Re-slugify from the translated title -- must be a plain .save(),
        # see docs/claude_context/seed_dev_data.md before changing this.
        en_page = translation.get_target_instance()
        new_slug = slugify(en_page.title)
        if new_slug and new_slug != en_page.slug:
            en_page.slug = find_available_slug(en_page.get_parent(), new_slug)
            en_page.save()

        self.created_count += 1
        self.stdout.write(
            f"  translated {type(nb_page).__name__} (en): {nb_page.title}"
        )
        return en_page

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

    def _sync_english_locale(self, nb_locale, en_locale):
        LocaleSynchronization.objects.get_or_create(
            locale=en_locale, defaults={"sync_from": nb_locale}
        )
        call_command("sync_locale_trees")
