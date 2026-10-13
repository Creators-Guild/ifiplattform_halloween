"""Models for small site-wide content, e.g. the rotating header message."""

from django.db import models
from django.utils.html import strip_tags
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import TranslatableMixin


class HeaderMessage(TranslatableMixin, models.Model):
    """A short message shown in the site header; one is picked at random per page load."""

    text = RichTextField(
        features=["bold", "italic", "link"],
        help_text="Short message shown in the site header, e.g. 'Lost? Need a map? Use IfiRom'.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this message without deleting it.",
    )

    panels = [
        FieldPanel("text"),
        FieldPanel("is_active"),
    ]

    def __str__(self):
        return strip_tags(self.text)[:60]
