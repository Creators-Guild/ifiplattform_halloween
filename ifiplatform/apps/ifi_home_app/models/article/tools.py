"""ToolPage -- fully standalone, no cross-references to any other page type."""

from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Page

from ..page_mixins import TranslationWarningMixin
from ...translation.english_overlay import EnglishPreviewMixin


# Model for an ifi-tool's own page (e.g. event calendar, map webpage)
class ToolPage(
    EnglishPreviewMixin, TranslationWarningMixin, Page
):  # pylint: disable=too-many-ancestors
    """A single ifi-tool's page: what it is, an image, an optional link and maker."""

    template = "info_articles/pages/tool_page.html"
    translated_fields = ["description"]

    description = RichTextField(help_text="What this tool is / what it does.")
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    image_overlay = models.BooleanField(
        default=True,
        help_text=(
            "Darken the image so the title/maker stay readable when overlaid on it. "
            "Turn off to show the image plain, with the title below it instead."
        ),
    )
    link = models.URLField(
        blank=True,
        help_text="Link to the tool itself, e.g. the calendar or map webpage.",
    )
    made_by = models.CharField(
        max_length=250,
        blank=True,
        help_text="Who made this tool, if relevant.",
    )
    preview_images = StreamField(
        [
            ("image", ImageChooserBlock()),
        ],
        use_json_field=True,
        blank=True,
        max_num=3,
        help_text="Up to three screenshots/previews of the tool, shown below the description.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("image"),
        FieldPanel("image_overlay"),
        FieldPanel("link"),
        FieldPanel("made_by"),
        FieldPanel("preview_images"),
    ]

    parent_page_types = ["ifi_home_app.ArticleIndexPage", "ifi_home_app.CategoryPage"]
    subpage_types = []  # tool pages have no children
