from django.contrib.sitemaps import Sitemap
from wagtail.models import Page


class IfiPlatformSitemap(Sitemap):
    """Every live, public Wagtail page, once per language: its /nb/ address
    and its /en/ address (English slugs), with hreflang alternates linking
    the two. Uses Django's own i18n sitemap support: each location() is
    built with that language active. depth=1 is the literal Wagtail Root
    node above any Site, not a real page -- excluded. .public() drops
    anything behind a Wagtail privacy/password restriction."""

    i18n = True
    languages = ["nb", "en"]
    alternates = True

    def items(self):
        return (
            Page.objects.live()
            .public()
            .exclude(depth=1)
            .order_by("path")
            .defer_streamfields()
            .specific()
        )

    def location(self, page):
        return page.get_url()

    def lastmod(self, page):
        return page.last_published_at or page.latest_revision_created_at
