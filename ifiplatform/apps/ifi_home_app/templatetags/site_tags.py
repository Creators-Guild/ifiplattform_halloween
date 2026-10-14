"""Template tags for small site-wide content, e.g. the rotating header message."""

from django import template
from django.utils import timezone, translation

from ..models.site_models import HeaderMessage

register = template.Library()

HEADER_MESSAGE_ROTATE_SECONDS = 600  # 10 minutes


@register.simple_tag
def get_header_message():
    """Return the active header message for the current 10-minute window --
    a stable pick (not randomized per request), so every visitor sees the
    same one at the same time regardless of which gunicorn worker or how
    many times they reload, and it advances to the next one every 10
    minutes on its own."""
    messages = list(HeaderMessage.objects.filter(is_active=True).order_by("pk"))
    if not messages:
        return None
    bucket = int(timezone.now().timestamp() // HEADER_MESSAGE_ROTATE_SECONDS)
    return messages[bucket % len(messages)]


@register.simple_tag(takes_context=True)
def translated_page_url(context, locale_code):
    """URL of the current Wagtail page in the given language: the same
    page, that language's address (English slugs under /en/). Falls back to
    the current path for non-Wagtail views (e.g. the home page), whose
    address Django's language switch translates by itself."""
    request = context.get("request")
    fallback = request.path if request else "/"
    page = context.get("page")
    if not page:
        return fallback
    with translation.override(locale_code):
        return page.get_url(request) or fallback
