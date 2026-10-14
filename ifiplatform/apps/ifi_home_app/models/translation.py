"""SegmentTranslation (the English for one piece of Norwegian text on a page
or snippet), EnglishSlug (a page's English address part), WaitingForEnglish
(objects DeepL still has to translate) and TranslationSettings.

Design rationale: docs/claude_context/translation_overlay.md"""

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.models import Page

SOURCE_CHOICES = [("deepl", "DeepL"), ("human", "Person")]


class SegmentTranslation(models.Model):
    """One row = "at this place on this page, this Norwegian text is this
    English text". Read and written only through
    translation/stored_translations.py."""

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    object_id = models.PositiveBigIntegerField()
    segment_path = models.TextField()
    norwegian_text = models.TextField()
    norwegian_hash = models.UUIDField()
    english_text = models.TextField()
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    translated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    has_error = models.BooleanField(default=False)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id", "segment_path", "norwegian_hash"],
                name="unique_segment_translation",
            )
        ]

    def __str__(self):
        return f"{self.segment_path}: {self.english_text[:50]}"

    def object_title(self):
        """The page/snippet this row belongs to, for the superuser list."""
        model = self.content_type.model_class()
        found = (
            model._default_manager.filter(pk=self.object_id).first() if model else None
        )
        return str(found) if found else f"(deleted {self.content_type.name})"

    object_title.short_description = "Page or snippet"


class EnglishSlug(models.Model):
    """The English slug of one page, used in its /en/ address. Its own table
    (not a page field), so the worker can set it without a page revision.
    Read and written only through translation/english_urls.py."""

    page = models.OneToOneField(Page, on_delete=models.CASCADE, related_name="+")
    slug = models.SlugField(max_length=255, allow_unicode=True)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.slug


class WaitingForEnglish(models.Model):
    """One page or snippet waiting for DeepL. Written on publish/save, read
    and deleted by `manage.py translate_english` (every minute). Only
    translation/auto_translate.py uses it."""

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    object_id = models.PositiveBigIntegerField()
    requested_at = models.DateTimeField()
    attempts = models.PositiveIntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    # A person asked for it ("Machine-translate subtree"): translated even
    # while automatic translation is off.
    requested_by_person = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id"], name="unique_waiting_for_english"
            )
        ]


@register_setting(icon="globe")
class TranslationSettings(BaseGenericSetting):
    """Superusers only (nobody else gets the change permission)."""

    auto_translate = models.BooleanField(
        default=True,
        verbose_name="Translate automatically with DeepL",
        help_text=(
            "On: English is filled in by DeepL when a page is published or a "
            "menu/message is saved, plus a nightly catch-up. Off: only the "
            '"Machine-translate now" button in the English editor calls '
            "DeepL. Switching back on: the nightly run fills in what's missing."
        ),
    )

    class Meta:
        verbose_name = "Translation settings"
