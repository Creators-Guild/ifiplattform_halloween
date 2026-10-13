"""Clears the site-wide cache (see settings.py's CACHES -- FileBasedCache,
persisted on disk under django_cache/ so it survives server restarts and,
notably, is NOT touched by `git reset --hard` during a deploy, since that
directory is untracked). Meant to run as part of every deploy, once the new
code is live -- without this, a value cached before the deploy can keep
being served after it, with nothing to invalidate it until it happens to
expire or get overwritten by chance.

Confirmed necessary the hard way: after some deploys, every Page.url
silently resolved to None (Wagtail's own site-root-paths cache had gone
stale relative to the actual page tree), turning every {% pageurl %} link
across the site into a literal "/en/None/"-style URL for every visitor,
since this cache is shared site-wide, not per-user.

Safe to run any time -- clearing a cache never loses real data, it just
means the next request recomputes whatever it needed."""

from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Clears the site-wide cache. Run as part of every deploy, once the new code is live."

    def handle(self, *args, **options):
        cache.clear()
        self.stdout.write(self.style.SUCCESS("Cache cleared."))
