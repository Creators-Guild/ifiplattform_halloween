"""Tracks when the DeepL glossary (see translation/glossary_terms.py and
the sync_deepl_glossary command) was last pushed, so the nightly
translate_english run can tell "this sentence's DeepL English predates the
current glossary" apart from "this sentence just hasn't changed" -- the
former is redone (the glossary may now translate it differently), the
latter isn't (stored_translations.forget_stale_glossary_rows)."""

from django.db import models


class GlossarySyncState(models.Model):
    """Singleton row (always pk=1) -- see touch()/last_synced_at()."""

    synced_at = models.DateTimeField(auto_now=True)

    @classmethod
    def touch(cls):
        """Call after successfully pushing a new glossary to DeepL."""
        obj, _ = cls.objects.get_or_create(pk=1)
        obj.save()  # bumps synced_at via auto_now even if just created
        return obj.synced_at

    @classmethod
    def last_synced_at(cls):
        """None if the glossary has never been synced from this app."""
        obj = cls.objects.filter(pk=1).first()
        return obj.synced_at if obj else None
