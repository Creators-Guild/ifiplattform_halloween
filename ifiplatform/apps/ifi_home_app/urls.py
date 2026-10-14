"""URL configuration for the ifi_home app."""

from django.urls import path, include
from wagtail import urls as wagtail_urls

from core_app.deploy_notice import deploy_notice_status_view
from .views import home_views
from .views import article_views
from .views import event_views

ifi_home_urlpatterns = [path("", home_views.main_view, name="ifi_home")]

ifi_api_urlpatterns = [
    path(
        "api/deploy-notice-status/",
        deploy_notice_status_view,
        name="deploy_notice_status",
    ),
    path(
        "api/articles/<int:page_id>/quick-style/",
        article_views.save_quick_style,
        name="article_quick_style",
    ),
    path(
        "api/articles/<int:page_id>/block-style/",
        article_views.save_block_style,
        name="article_block_style",
    ),
    path(
        "api/articles/<int:page_id>/header-style/",
        article_views.save_header_style,
        name="article_header_style",
    ),
    path(
        "api/articles/<int:page_id>/hero-image-style/",
        article_views.save_hero_image_style,
        name="article_hero_image_style",
    ),
    path(
        "api/articles/<int:page_id>/toc-icon-style/",
        article_views.save_toc_icon_style,
        name="article_toc_icon_style",
    ),
    path(
        "api/articles/<int:page_id>/publish/",
        article_views.publish_page,
        name="article_publish",
    ),
    path(
        "api/articles/<int:page_id>/unpublish/",
        article_views.unpublish_page,
        name="article_unpublish",
    ),
    # not article-specific -- CategoryPage/ArticleIndexPage's own title
    # banner, see BannerStyleMixin/PageBannerStyle in article_models.py.
    path(
        "api/pages/<int:page_id>/banner-style/",
        article_views.save_banner_style,
        name="page_banner_style",
    ),
    # Not page-scoped -- triggers the site-wide sync_peoply_events command,
    # see event_views.force_sync_peoply_events.
    path(
        "api/peoply/force-sync/",
        event_views.force_sync_peoply_events,
        name="force_sync_peoply_events",
    ),
]

ifi_article_urlpatterns = [
    path("", include(wagtail_urls)),
]

urlpatterns = ifi_home_urlpatterns + ifi_api_urlpatterns + ifi_article_urlpatterns
