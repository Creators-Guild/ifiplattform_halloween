"""Seeds the Halloween mock site with a bare-minimum, Halloween-themed page
tree: the dev seed's categories, unions and menus, plus one article per
category, two news articles, three events, one tool and a banner. The
commit event is about filling the site in, so it's deliberately sparse.

Runs as SEED_COMMAND from deploy/docker/deploy.sh on every deploy, but
only seeds an empty site: once the hub ArticleIndexPage exists it does
nothing, so edits made in wagtail-admin survive later deploys. The whole
run is one transaction, so a crash leaves nothing half-seeded.

Creates no users at all -- the organiser makes the superuser by hand with
createsuperuser. Every page gets English like seed_dev_data's (see
SeedHelpersMixin._translate_page)."""

from datetime import date, datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from wagtail.models import Locale, Page
from wagtail.rich_text import RichText

from ifi_home_app.management.seed_dev_data.helpers import SeedHelpersMixin
from ifi_home_app.management.seed_dev_data.menus import MenuSeedMixin
from ifi_home_app.management.seed_dev_data.unions import UnionSeedMixin
from ifi_home_app.models import (
    ArticleIndexPage,
    ArticlePage,
    EventIndexPage,
    EventPage,
    HeaderMessage,
    HomeBoardMessage,
)
from ifi_home_app.models.article_models import CategoryPage, ToolPage
from ifi_home_app.translation import page_segments

from .constants import (
    ARTICLE_SPECS,
    BANNER_TEXT,
    BOARD_MESSAGE_SPECS,
    CATEGORY_SPECS,
    EVENT_LOCATION,
    EVENT_SPECS,
    NEW_STUDENT_ARTICLE_SPEC,
    NEWS_SPECS,
    SAME_IN_ENGLISH,
    TOOL_SPEC,
    TRANSLATIONS,
)

_STORED_TRANSLATIONS = {
    page_segments.stored_form(norwegian): page_segments.stored_form(english)
    for norwegian, english in TRANSLATIONS.items()
}
_STORED_SAME = {page_segments.stored_form(text) for text in SAME_IN_ENGLISH}


class HalloweenHelpersMixin(SeedHelpersMixin):
    def _english_for(self, stored_text):
        if stored_text in TRANSLATIONS:
            return TRANSLATIONS[stored_text]
        if stored_text in _STORED_TRANSLATIONS:
            return _STORED_TRANSLATIONS[stored_text]
        if stored_text in SAME_IN_ENGLISH or stored_text in _STORED_SAME:
            return stored_text
        return None


class Command(HalloweenHelpersMixin, UnionSeedMixin, MenuSeedMixin, BaseCommand):
    help = (
        "Seeds an empty database with the Halloween mock site's bare-minimum "
        "page tree. Does nothing if the site is already seeded. Creates no users."
    )

    def handle(self, *args, **options):
        if ArticleIndexPage.objects.filter(section="hub").exists():
            self.stdout.write("Already seeded, nothing to do.")
            return

        self.created_count = 0
        self.skipped_count = 0
        with transaction.atomic():
            self._seed()
        self.stdout.write(
            self.style.SUCCESS(f"Done: {self.created_count} object(s) created.")
        )

    def _seed(self):
        nb_locale, _ = Locale.objects.get_or_create(language_code="nb")
        seed_image = self._get_or_create_seed_image()
        root = Page.get_first_root_node()

        artikkler = self._page(
            root, ArticleIndexPage, "Artikkler", nb_locale, section="hub"
        )
        self._set_default_site_root(artikkler)

        nyheter = self._page(
            artikkler, ArticleIndexPage, "Nyheter", nb_locale, section="news"
        )
        news_category = self._page(
            nyheter, CategoryPage, "Siste nytt", nb_locale, color="pink"
        )
        today = timezone.now().date()
        for title, intro, heading, text, days_ago in NEWS_SPECS:
            self._article(
                news_category, title, intro, heading, text, nb_locale,
                published_date=today - timedelta(days=days_ago),
            )

        info_articles = self._page(
            artikkler,
            ArticleIndexPage,
            "Informasjonsartikkler",
            nb_locale,
            section="info_articles",
        )
        for title, color in CATEGORY_SPECS:
            category = self._page(
                info_articles, CategoryPage, title, nb_locale, color=color
            )
            self._article(category, *ARTICLE_SPECS[title], nb_locale)

            if title == "Sosialt":
                self._seed_student_unions(category, nb_locale, seed_image)
                self._seed_fadderuke_unions(nb_locale, seed_image)
            elif title == "Praktisk":
                self._seed_halloween_tool(category, nb_locale, seed_image)
                self._seed_halloween_new_student(category, nb_locale, seed_image)

        self._seed_halloween_events(artikkler, nb_locale)
        self._seed_halloween_messages(nb_locale)
        self._seed_menus(nb_locale)

    def _page(self, parent, model, title, locale, **kwargs):
        page = self._get_or_create_page(parent, model, title, locale, **kwargs)
        self._translate_page(page)
        return page

    def _article(self, category, title, intro, heading, text, locale, **kwargs):
        return self._page(
            category,
            ArticlePage,
            title,
            locale,
            intro=intro,
            published_date=kwargs.pop("published_date", timezone.now().date()),
            body=self._build_article_body(heading, text),
            **kwargs,
        )

    def _seed_halloween_tool(self, praktisk, nb_locale, seed_image):
        # Slug pinned, like seed_dev_data/tools.py: the menus look it up by it.
        tool_category = self._page(
            praktisk,
            CategoryPage,
            "Ifi verktøy",
            nb_locale,
            color="turq",
            slug="ifi-verktøy",
        )
        self._page(
            tool_category,
            ToolPage,
            TOOL_SPEC["title"],
            nb_locale,
            description=TOOL_SPEC["description"],
            image=seed_image,
            link="https://example.com",
            made_by="Ifi Platform",
        )

    def _seed_halloween_new_student(self, praktisk, nb_locale, seed_image):
        category = self._page(
            praktisk,
            CategoryPage,
            "Ny Ifi Student?",
            nb_locale,
            slug="ny-ifi-student",
            color="turq",
            intro="Her er alt du skulle trenge som en ny Ifi Student!",
        )
        self._article(
            category, *NEW_STUDENT_ARTICLE_SPEC, nb_locale, hero_image=seed_image
        )

    def _seed_halloween_events(self, artikkler, nb_locale):
        event_index = self._page(artikkler, EventIndexPage, "Arrangementer", nb_locale)
        today = timezone.now().date()
        halloween = date(today.year, 10, 31)
        if halloween < today:
            halloween = date(today.year + 1, 10, 31)
        for title, event_type, days_before, time_str in EVENT_SPECS:
            self._page(
                event_index,
                EventPage,
                title,
                nb_locale,
                event_type=event_type,
                event_date=halloween - timedelta(days=days_before),
                event_time=(
                    datetime.strptime(time_str, "%H:%M").time() if time_str else None
                ),
                location=EVENT_LOCATION,
            )

    def _seed_halloween_messages(self, nb_locale):
        banner = HeaderMessage.objects.create(
            text=RichText(f"<p>{BANNER_TEXT}</p>"), is_active=True, locale=nb_locale
        )
        self._translate_page(banner)
        self.created_count += 1

        for i, spec in enumerate(BOARD_MESSAGE_SPECS):
            message = HomeBoardMessage.objects.create(
                title=spec["title"],
                date=timezone.now().date(),
                body=RichText(spec["body"]),
                sender_name=spec["sender_name"],
                sender_role="Seed script",
                order=i,
                display_seconds=spec["display_seconds"],
                locale=nb_locale,
            )
            self._translate_page(message)
            self.created_count += 1
