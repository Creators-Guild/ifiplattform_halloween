"""English slugs: storing them, building /en/ addresses from them, routing
/en/ requests by them, and redirecting when one changes. The only code that
reads or writes the EnglishSlug table.

install() puts routing and links on Wagtail's own Page (route() and
get_url_parts()), so every page type and plain Page objects (breadcrumbs,
child lists) get English addresses under /en/, and connects the redirects
for moved pages and changed Norwegian slugs.

Design rationale: docs/claude_context/translation_overlay.md"""

from contextlib import contextmanager
from contextvars import ContextVar

from django.conf import settings
from django.http import Http404
from django.urls import reverse
from django.utils import translation
from django.utils.text import slugify
from wagtail.contrib.redirects.models import Redirect
from wagtail.contrib.redirects import signal_handlers as redirect_signal_handlers
from wagtail.models import Page
from wagtail.signals import page_slug_changed, post_page_move, pre_page_move

from ..models.translation import EnglishSlug

_request_memo = ContextVar("english_urls_memo", default=None)


@contextmanager
def request_scope():
    """Inside this block (one request), English slugs and the page tree are
    loaded at most once, so a list of cards doesn't query per link."""
    token = _request_memo.set({})
    try:
        yield
    finally:
        _request_memo.reset(token)


def _remembered(key, load):
    memo = _request_memo.get()
    if memo is None:
        return load()
    if key not in memo:
        memo[key] = load()
    return memo[key]


def _forget_slugs():
    memo = _request_memo.get()
    if memo is not None:
        memo.pop("slugs", None)


def _english_slugs():
    """{page id: English slug} for every page that has one."""
    return _remembered(
        "slugs", lambda: dict(EnglishSlug.objects.values_list("page_id", "slug"))
    )


def _tree():
    """{treebeard path: (page id, Norwegian slug)} for every page."""
    return _remembered(
        "tree",
        lambda: {
            path: (pk, slug)
            for path, pk, slug in Page.objects.values_list("path", "pk", "slug")
        },
    )


def english_slug(page):
    """`page`'s English slug, or None if it has none yet."""
    return _english_slugs().get(page.pk)


def path_slug(page_id, norwegian_slug):
    """The slug used in a page's /en/ address: English, else Norwegian."""
    return _english_slugs().get(page_id) or norwegian_slug


def english_url_path(page, root_depth):
    """`page`'s path below its site root (at `root_depth`) with English
    slugs, e.g. "student-life/freshers-week/". Empty for the root itself."""
    tree, step = _tree(), Page.steplen
    parts = []
    for depth in range(root_depth + 1, page.depth + 1):
        pk, slug = tree[page.path[: depth * step]]
        parts.append(path_slug(pk, slug) + "/")
    return "".join(parts)


def find_child(parent, slug):
    """For routing under /en/: (child, by_english). The child of `parent`
    whose English slug is `slug`, else the one whose Norwegian slug is, with
    by_english False. (None, False) if neither exists."""
    children = parent.get_children()
    english_ids = [pk for pk, english in _english_slugs().items() if english == slug]
    child = children.filter(pk__in=english_ids).first() if english_ids else None
    if child is not None:
        return child, True
    return children.filter(slug=slug).first(), False


# --- Routing and links on Wagtail's Page -------------------------------------


class MovedToEnglishAddress(Exception):
    """A Norwegian slug under /en/ for a page that has an English slug.
    english_overlay.EnglishDisplayMiddleware turns it into a permanent
    redirect to the English address."""

    def __init__(self, page, rest):
        super().__init__(page.pk)
        self.page, self.rest = page, rest

    def url(self, request):
        with translation.override("en"):
            base = self.page.get_url(request) or "/en/"
        return base + "".join(f"{part}/" for part in self.rest)


def wants_english_address():
    """Addresses follow the language prefix (Django's active language), not
    english_active(): every link built under /en/ uses English slugs, also
    on POST/AJAX where English text is off."""
    return translation.get_language() == "en"


_original_route = Page.route
_original_get_url_parts = Page.get_url_parts


def _route(self, request, path_components):
    if not path_components or not wants_english_address():
        return _original_route(self, request, path_components)
    child, by_english = find_child(self, path_components[0])
    if child is None:
        raise Http404
    if not by_english and english_slug(child):
        raise MovedToEnglishAddress(child, path_components[1:])
    child._cached_parent_obj = self
    return child.specific.route(request, path_components[1:])


def _get_url_parts(self, request=None):
    parts = _original_get_url_parts(self, request=request)
    if not parts or parts[2] is None or not wants_english_address():
        return parts
    site_id, root_url, _ = parts
    root_paths = [
        root
        for root in self._get_relevant_site_root_paths(request)
        if root.site_id == site_id
    ]
    if not root_paths:
        return parts
    root_depth = root_paths[0].root_path.rstrip("/").count("/") + 1
    try:
        relative = english_url_path(self, root_depth)
    except KeyError:  # not saved in the tree yet (e.g. a new page's preview)
        return parts
    return site_id, root_url, reverse("wagtail_serve", args=(relative,))


def install():
    """Called once from IfiHomeAppConfig.ready()."""
    Page.route = _route
    Page.get_url_parts = _get_url_parts
    redirect_signal_handlers.create_redirects = _create_redirects_in_norwegian
    pre_page_move.connect(_before_page_move, dispatch_uid="english_before_move")
    post_page_move.connect(_after_page_move, dispatch_uid="english_after_move")
    page_slug_changed.connect(_after_slug_change, dispatch_uid="english_slug_change")


# --- Changing English slugs ---------------------------------------------------


def _english_urls(page):
    """{page id: English address} for `page` and its live descendants."""
    pages = [page] + list(page.get_descendants().live())
    with translation.override("en"):
        return {each.pk: each.get_url() for each in pages}


def _redirect(old, new):
    Redirect.objects.update_or_create(
        old_path=Redirect.normalise_path(old),
        site=None,
        defaults={
            "redirect_link": new,
            "redirect_page": None,
            "is_permanent": True,
            "automatically_created": True,
        },
    )


def _redirect_changed(before, after):
    for page_id, old in before.items():
        new = after.get(page_id)
        if old and new and old != new:
            _redirect(old, new)


def set_english_slug(page, wanted, source, user=None, redirect=True):
    """Saves `page`'s English slug from `wanted` (any text, slugified), made
    unique among its siblings with -2, -3, ...: never equal to a sibling's
    English slug or Norwegian slug (the fallback address). If the English
    addresses of a live page and its descendants change, the old ones
    redirect to the new. Returns the slug saved."""
    base = slugify(wanted, allow_unicode=True) or page.slug
    siblings = page.get_siblings(inclusive=False)
    taken = set(siblings.values_list("slug", flat=True))
    taken.update(
        EnglishSlug.objects.filter(page__in=siblings).values_list("slug", flat=True)
    )
    slug, number = base, 1
    while slug in taken:
        number += 1
        slug = f"{base}-{number}"
    with request_scope():
        before = _english_urls(page) if redirect and page.live else {}
        EnglishSlug.objects.update_or_create(
            page_id=page.pk,
            defaults={"slug": slug, "source": source, "updated_by": user},
        )
        _forget_slugs()
        after = _english_urls(page) if before else {}
    _forget_slugs()
    _redirect_changed(before, after)
    return slug


def set_english_slug_if_missing(page, english_title):
    """Sets the slug once, from the first English title (DeepL). Later title
    changes keep it, so English addresses stay stable."""
    if english_slug(page) is None:
        return set_english_slug(page, english_title, "deepl")
    return None


# --- Moved pages and changed Norwegian slugs ---------------------------------
# Wagtail's own redirects (wagtail.contrib.redirects) compare a page's old and
# new address. Under "en" our get_url_parts() reads the tree as it is now, so
# both look the same, and its empty batch then deletes EVERY automatically
# created redirect (BatchRedirectCreator.pre_process filters on an empty Q).
# So Wagtail's part always runs in Norwegian, and these add the English.

_wagtail_create_redirects = redirect_signal_handlers.create_redirects


def _create_redirects_in_norwegian(*args, **kwargs):
    with translation.override(settings.LANGUAGE_CODE):
        return _wagtail_create_redirects(*args, **kwargs)


_english_before_move = {}


def _before_page_move(instance, url_path_before, url_path_after, **kwargs):
    if url_path_before != url_path_after and instance.live:
        with request_scope():
            _english_before_move[instance.pk] = _english_urls(instance)


def _after_page_move(instance, **kwargs):
    before = _english_before_move.pop(instance.pk, None)
    if before:
        with request_scope():
            _redirect_changed(before, _english_urls(instance))


def _after_slug_change(instance_before, instance, **kwargs):
    """Without an English slug, a page's /en/ address uses its Norwegian
    slug, so the English addresses move with it."""
    if not instance.live:
        return
    with request_scope():
        if english_slug(instance) is not None:
            return
        after = _english_urls(instance)
    new_prefix = after.get(instance.pk) or ""
    if not new_prefix.endswith(f"/{instance.slug}/"):
        return
    old_prefix = new_prefix[: -len(instance.slug) - 1] + f"{instance_before.slug}/"
    before = {
        pk: old_prefix + url[len(new_prefix) :]
        for pk, url in after.items()
        if url and url.startswith(new_prefix)
    }
    _redirect_changed(before, after)
