"""Dummy data for populating NewsItem objects during development."""

from ..models.home_models import NewsItem


def create(fresh_on_page_load: bool = False):
    """Create dummy NewsItem entries, optionally clearing existing ones first."""
    if fresh_on_page_load:
        NewsItem.objects.all().delete()

    NewsItem.objects.bulk_create(
        [
            NewsItem(
                title="Welcome to the platform",
                description="This is a demo news item to test the news bar.",
                image_name="IfiBygg.jpg",
            ),
            NewsItem(
                title="Second news item",
                description="Another example item, automatically created.",
                image_name="IfiBygg.jpg",
            ),
            NewsItem(
                title="Third news item",
                description="You can replace these with real content later.",
                image_name="IfiBygg.jpg",
            ),
            NewsItem(
                title="Fourth news item",
                description="This is just test data for development.",
                image_name="IfiBygg.jpg",
            ),
        ]
    )
