"""Tool-page seeding under Praktisk: the demo tool (with a nested tool to
demonstrate CategoryPage.show_nested_tools), and the "Ny Ifi Student?" demo
articles."""

from django.utils import timezone

from ifi_home_app.models import ArticlePage
from ifi_home_app.models.article_models import CategoryPage, ToolPage

from .constants import NEW_STUDENT_ARTICLE_SPECS


class ToolSeedMixin:
    def _seed_tool(self, praktisk_category, nb_locale, seed_image):
        # Slug pinned explicitly -- plain slugify() would strip the "ø", and
        # menus.py (and existing databases) look this category up by it.
        # show_nested_tools=True so this category's own page also
        # demonstrates CategoryPage.show_nested_tools (article_models.py):
        # the tool below (nested_tool_category's own direct child, i.e. this
        # category's *grandchild*) shows up here alongside Test-verktøy,
        # not just on nested_tool_category's own page.
        tool_category = self._get_or_create_page(
            praktisk_category,
            CategoryPage,
            "Ifi verktøy",
            nb_locale,
            color="turq",
            slug="ifi-verktøy",
            show_nested_tools=True,
        )
        self._translate_page(tool_category)

        tool = self._get_or_create_page(
            tool_category,
            ToolPage,
            "Test-verktøy",
            nb_locale,
            description="Et test-verktøy generert av seed-scriptet.",
            image=seed_image,
            image_overlay=True,
            link="https://example.com",
            made_by="Ifi Platform",
            preview_images=[("image", seed_image)],
        )
        self._translate_page(tool)

        nested_tool_category = self._get_or_create_page(
            tool_category,
            CategoryPage,
            "UiO verktøy",
            nb_locale,
            color="pink",
            slug="uio-verktoy",
        )
        self._translate_page(nested_tool_category)

        nested_tool = self._get_or_create_page(
            nested_tool_category,
            ToolPage,
            "Nøstet test-verktøy",
            nb_locale,
            description=(
                "Et nøstet test-verktøy generert av seed-scriptet, for å "
                'vise Ifi verktøy sin "vis nøstede verktøy"-innstilling.'
            ),
            image=seed_image,
            link="https://example.com",
            made_by="Ifi Platform",
        )
        self._translate_page(nested_tool)

    def _seed_new_student_articles(self, praktisk_category, nb_locale, seed_image):
        # Slug pinned explicitly, like "ifi-verktøy" above -- menus.py looks
        # this category up by it for the "New Student?" menu group.
        new_student_category = self._get_or_create_page(
            praktisk_category,
            CategoryPage,
            "Ny Ifi Student?",
            nb_locale,
            slug="ny-ifi-student",
            color="turq",
            intro="Her er alt du skulle trenge som en ny Ifi Student!",
        )
        self._translate_page(new_student_category)

        today = timezone.now().date()
        for title, intro, heading, text in NEW_STUDENT_ARTICLE_SPECS:
            article = self._get_or_create_page(
                new_student_category,
                ArticlePage,
                title,
                nb_locale,
                intro=intro,
                published_date=today,
                hero_image=seed_image,
                body=self._build_article_body(heading, text),
            )
            self._translate_page(article)
