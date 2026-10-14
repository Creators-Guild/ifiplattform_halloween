"""News article seeding under the Nyheter index."""

from datetime import timedelta

from django.utils import timezone

from ifi_home_app.models import ArticlePage
from ifi_home_app.models.article_models import CategoryPage

from .constants import NEWS_ARTICLE_TITLES


class NewsSeedMixin:
    def _seed_news_articles(self, nyheter, nb_locale):
        # ArticlePage.parent_page_types only allows a CategoryPage parent, so
        # the news articles need a category under Nyheter to live in.
        news_category = self._get_or_create_page(
            nyheter,
            CategoryPage,
            "Siste nytt",
            nb_locale,
            color="pink",
        )
        self._translate_page(news_category)

        today = timezone.now().date()
        for i, title in enumerate(NEWS_ARTICLE_TITLES, start=1):
            article = self._get_or_create_page(
                news_category,
                ArticlePage,
                title,
                nb_locale,
                intro="En test-nyhetsartikkel generert av seed-scriptet.",
                published_date=today - timedelta(days=i),
                body=self._build_article_body(),
            )
            self._translate_page(article)
