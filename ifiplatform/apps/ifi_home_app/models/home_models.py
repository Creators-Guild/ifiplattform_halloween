"""Models for IFI home page: StudentUnion, IfiTool and the home message board."""

from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import TranslatableMixin


class StudentUnion(models.Model):
    """Represents a student union or organization at IFI."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image_name = models.CharField(max_length=100, blank=True)  # path to image in static
    programme_union = models.BooleanField(
        default=False, verbose_name="Is_programme_union"
    )
    homepage = models.URLField(blank=True)


class IfiTool(models.Model):
    """Represents a tool or resource created by IFI students/staff."""

    title = models.CharField(max_length=200)
    creators = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=200, blank=True)
    image_name = models.CharField(max_length=100, blank=True)  # path to image in static
    link = models.URLField(blank=True)


# temp item
class NewsItem(models.Model):
    """A temporary news item shown on the homepage, until a real news system exists."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image_name = models.CharField(max_length=100, blank=True)  # path to image in static
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class HomeBoardMessage(TranslatableMixin, models.Model):
    """A rotating message shown in the homepage message board (greetings, promotions, etc.)."""

    title = models.CharField(max_length=200)
    date = models.DateField(
        help_text="Date shown on the message, e.g. when it was posted or the event date."
    )
    body = RichTextField(features=["bold", "italic", "link"])
    sender_name = models.CharField(max_length=200, blank=True)
    sender_role = models.CharField(
        max_length=200,
        blank=True,
        help_text="e.g. 'Styreleder av IFI-Creators' Guild'.",
    )
    order = models.PositiveIntegerField(
        default=0, help_text="Messages are shown in ascending order."
    )
    display_seconds = models.PositiveIntegerField(
        default=8,
        help_text="How long this message is shown before auto-advancing to the next one, in seconds.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this message without deleting it.",
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("date"),
        FieldPanel("body"),
        FieldPanel("sender_name"),
        FieldPanel("sender_role"),
        FieldPanel("order"),
        FieldPanel("display_seconds"),
        FieldPanel("is_active"),
    ]

    class Meta:
        ordering = ["order", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=("translation_key", "locale"),
                name="unique_translation_key_locale_ifi_home_app_homeboardmessage",
            )
        ]

    def __str__(self):
        return self.title
