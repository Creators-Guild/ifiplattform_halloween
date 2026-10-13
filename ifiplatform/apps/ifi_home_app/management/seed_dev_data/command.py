"""Seeds a fresh local-dev database with a minimal, representative Wagtail
page tree, so contributors don't have to hand-build the site structure
(index pages, categories, a student union, a tool, ...) every time they
start on a new checkout. Every nb page gets a real English translation,
submitted and imported through wagtail_localize's own PO pipeline rather
than a hand-written second copy of every field (see SeedHelpersMixin.
_translate_page).

Safe to re-run: every page is looked up by (parent, slug, locale) before
creation, so running this twice does not create duplicates.

Split into one mixin per content area (unions.py/news.py/events.py/
tools.py/messages.py) plus generic helpers.py, combined here into one
Command -- every seeding method is still called as a plain self._seed_x(...)
regardless of which mixin actually defines it."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from wagtail.models import Locale, Page

from ifiplatform.apps.ifi_home_app.models import ArticleIndexPage, ArticlePage
from ifiplatform.apps.ifi_home_app.models.article_models import CategoryPage

from .constants import CATEGORY_SPECS
from .events import EventSeedMixin
from .helpers import SeedHelpersMixin
from .menus import MenuSeedMixin
from .messages import MessageSeedMixin
from .news import NewsSeedMixin
from .tools import ToolSeedMixin
from .unions import UnionSeedMixin
from .users import UserSeedMixin


class Command(
    SeedHelpersMixin,
    UnionSeedMixin,
    NewsSeedMixin,
    EventSeedMixin,
    ToolSeedMixin,
    MessageSeedMixin,
    MenuSeedMixin,
    UserSeedMixin,
    BaseCommand,
):
    help = (
        "Populates the local dev database with a dummy nb article tree "
        "(index pages, categories, a test article per category, a student "
        "union category with two unions, and a tool page) plus an admin/admin superuser, each translated "
        "into a real en counterpart via wagtail_localize's PO pipeline. "
        "Re-running is a no-op for anything that already exists."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow running even when DEBUG is off (e.g. against a real Postgres db).",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "DEBUG is off -- refusing to seed dummy data into what looks like a "
                "non-local database. Pass --force if you really mean it."
            )

        self.created_count = 0
        self.skipped_count = 0

        self._seed_dev_superuser()

        # Deliberately not wrapped in transaction.atomic(): Translation.save_target()
        # defers its actual page-content publish via transaction.on_commit(), which
        # only fires when the OUTERMOST transaction commits. Wrapping this whole
        # method in one atomic() block would queue up every page's deferred publish
        # until the very end, where each one re-applies its (pre-slug-fix) frozen
        # revision and silently reverts the slug rewrite in _translate_page below.
        # Without an enclosing transaction, each on_commit fires immediately.
        nb_locale, _ = Locale.objects.get_or_create(language_code="nb")
        en_locale, _ = Locale.objects.get_or_create(language_code="en")

        seed_image = self._get_or_create_seed_image()

        root = Page.get_first_root_node()

        artikkler = self._get_or_create_page(
            root,
            ArticleIndexPage,
            "Artikkler",
            nb_locale,
            section="hub",
        )
        self._set_default_site_root(artikkler)
        self._translate_page(artikkler, en_locale)

        nyheter = self._get_or_create_page(
            artikkler,
            ArticleIndexPage,
            "Nyheter",
            nb_locale,
            section="news",
        )
        self._translate_page(nyheter, en_locale)
        self._seed_news_articles(nyheter, nb_locale, en_locale)

        info_articles = self._get_or_create_page(
            artikkler,
            ArticleIndexPage,
            "Informasjonsartikkler",
            nb_locale,
            section="info_articles",
        )
        self._translate_page(info_articles, en_locale)

        for title, color in CATEGORY_SPECS:
            category = self._get_or_create_page(
                info_articles,
                CategoryPage,
                title,
                nb_locale,
                color=color,
            )
            self._translate_page(category, en_locale)

            article = self._get_or_create_page(
                category,
                ArticlePage,
                "Testartikkel",
                nb_locale,
                intro="En test-artikkel generert av seed-scriptet.",
                published_date=timezone.now().date(),
                body=self._build_article_body(),
            )
            self._translate_page(article, en_locale)

            if title == "Sosialt":
                self._seed_student_unions(category, nb_locale, en_locale, seed_image)
            elif title == "Praktisk":
                self._seed_tool(category, nb_locale, en_locale, seed_image)
                self._seed_new_student_articles(
                    category, nb_locale, en_locale, seed_image
                )

        self._seed_events(artikkler, nb_locale, en_locale, seed_image)

        self._sync_english_locale(nb_locale, en_locale)

        self._seed_header_message(nb_locale, en_locale)
        self._seed_home_board_message(nb_locale, en_locale)
        self._seed_menus(nb_locale, en_locale)

        # wagtail_localize's copy-for-translation path doesn't keep the
        # translated parent's `numchild` counter in sync, which makes
        # Wagtail's tree-walking router treat every en page as childless
        # (silent 404s below the site root). fix_tree() recalculates it.
        Page.fix_tree()

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {self.created_count} page(s) created, "
                f"{self.skipped_count} already existed."
            )
        )
