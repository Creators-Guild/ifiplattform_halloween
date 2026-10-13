from wagtail.contrib.sitemaps import Sitemap as WagtailSitemap
from wagtail.models import Page


class IfiPlatformSitemap(WagtailSitemap):
    """Every live, public Wagtail page across both locales, for /sitemap.xml.

    Wagtail's own Sitemap.items() only walks the *default* Site's
    root_page descendants -- but this project has one Site record whose
    root_page is the 'nb' locale tree, with the 'en' translation living
    under its own separate root page (a sibling, not a descendant of the
    'nb' one -- see wagtail_localize's per-locale page trees). Querying
    Page directly picks up both. depth=1 is the literal Wagtail Root node
    above any Site, not a real page -- excluded. .public() drops anything
    behind a Wagtail privacy/password restriction.
    """

    def items(self):
        return (
            Page.objects.live()
            .public()
            .exclude(depth=1)
            .order_by("path")
            .defer_streamfields()
            .specific()
        )
