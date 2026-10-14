# pylint: disable=C0114,C0115,C0116
import os
import re
import time

from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, RequestFactory, TestCase, TransactionTestCase, tag
from django.urls import reverse

from core_app.deploy_notice import deploy_notice


class DeployNoticeTests(TestCase):
    """Covers the read side (deploy_notice context processor) of the
    site-wide deploy countdown banner -- see announce_deploy (the write
    side) and templates/partials/deploy_notice.html (the render side, one
    include in global_base.html covering every page)."""

    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()

    def test_no_active_announcement_is_none(self):
        request = self.factory.get("/")
        self.assertIsNone(deploy_notice(request)["deploy_notice_target"])

    def test_announce_deploy_sets_the_target_the_processor_reads(self):
        before = int(time.time())
        call_command("announce_deploy", "--minutes", "10")
        after = int(time.time())

        request = self.factory.get("/")
        target = deploy_notice(request)["deploy_notice_target"]

        self.assertIsNotNone(target)
        # target should be ~10 minutes from whenever the command actually
        # ran, not off by an unrelated amount.
        self.assertGreaterEqual(target, before + 10 * 60)
        self.assertLessEqual(target, after + 10 * 60)

    def test_clear_removes_an_active_announcement(self):
        call_command("announce_deploy", "--minutes", "10")
        call_command("announce_deploy", "--clear")

        request = self.factory.get("/")
        self.assertIsNone(deploy_notice(request)["deploy_notice_target"])

    def test_clear_is_a_safe_no_op_with_nothing_announced(self):
        call_command("announce_deploy", "--clear")

        request = self.factory.get("/")
        self.assertIsNone(deploy_notice(request)["deploy_notice_target"])


class DeployNoticeStatusViewTests(TestCase):
    """The endpoint deploy_notice.js polls from already-open tabs (see that
    file's own poll()) -- what makes an announcement appear/disappear
    without the visitor reloading or navigating anywhere."""

    def setUp(self):
        cache.clear()

    def test_no_active_announcement_returns_null_target(self):
        response = self.client.get(reverse("deploy_notice_status"))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["target"])

    def test_active_announcement_returns_the_target(self):
        call_command("announce_deploy", "--minutes", "10")
        response = self.client.get(reverse("deploy_notice_status"))
        self.assertIsNotNone(response.json()["target"])

    def test_cleared_announcement_returns_null_again(self):
        call_command("announce_deploy", "--minutes", "10")
        call_command("announce_deploy", "--clear")
        response = self.client.get(reverse("deploy_notice_status"))
        self.assertIsNone(response.json()["target"])


class StaticReferenceTests(TestCase):
    """Every {% static '...' %} path in the project's own templates must
    exist. Tests run with plain StaticFilesStorage (see STORAGES in
    settings.py), which never checks, while production's manifest storage
    raises on a missing file -- so a stale path (e.g. left behind by a CSS
    folder rename) 500s every page that uses it in production only."""

    STATIC_TAG_RE = re.compile(r"""\{%\s*static\s+['"]([^'"]+)['"]""")
    # Pre-existing, study_app is hidden behind APPS_UNDER_DEVELOPMENT.
    KNOWN_MISSING = {
        "styles/neon_style/ifi_study/flashcards.css",
        "styles/neon_style/ifi_study/multiplechoice.css",
        "styles/neon_style/ifi_study/studygames.css",
    }

    def _project_template_dirs(self):
        base_dir = Path(settings.BASE_DIR)
        dirs = [Path(d) for d in settings.TEMPLATES[0]["DIRS"]]
        for app in apps.get_app_configs():
            app_templates = Path(app.path) / "templates"
            if base_dir in app_templates.parents and app_templates.is_dir():
                dirs.append(app_templates)
        return dirs

    def test_every_static_reference_exists(self):
        missing = []
        for template_dir in self._project_template_dirs():
            for template in template_dir.rglob("*.html"):
                for path in self.STATIC_TAG_RE.findall(
                    template.read_text(encoding="utf-8")
                ):
                    if path not in self.KNOWN_MISSING and finders.find(path) is None:
                        missing.append(
                            f"{path} (in {template.relative_to(settings.BASE_DIR)})"
                        )
        self.assertEqual(
            missing, [], "Templates reference static files that don't exist"
        )


@tag("slow")
class SiteCrawlTests(TransactionTestCase):
    """Crawls the whole public site starting from each locale's homepage
    (one subtest per locale in settings.LANGUAGES; limit it with e.g.
    CRAWL_LOCALES=en or CRAWL_LOCALES=en,nb), following every internal link
    it finds, and fails if any of them is broken or leads into another
    locale. Exists because of a real incident: a stale Wagtail
    site-root-paths cache silently turned every {% pageurl %} link on the
    site into a literal href="None" -- nothing caught it until someone
    clicked around by hand. See clear_cache's own docstring for the root
    cause.

    Only follows same-origin links, skipping static/media/admin and
    anything that isn't a path (external links, mailto:, "#", ...).
    href="" is a deliberate placeholder convention on this site (sections
    not built yet -- see APPS_UNDER_DEVELOPMENT), so it's not treated as
    broken; a literal href="None" always is, since that can only come from
    a template tag that failed to resolve a real page's URL.

    TransactionTestCase, not TestCase, so seed_dev_data runs with real
    commits and its on_commit callbacks (Wagtail's page_slug_changed, ...)
    fire the way they do on a real database."""

    HREF_RE = re.compile(r'href="([^"]*)"')
    EXCLUDED_PREFIXES = ("/static/", "/media/", "/admin/", "/wagtail-admin/")
    # Safety net against a runaway crawl (e.g. a link cycle), not a real
    # expectation -- seed_dev_data's tree is intentionally small.
    MAX_PAGES = 300

    def setUp(self):
        # --force: seed_dev_data refuses to run with DEBUG off, which the
        # test runner always forces regardless of .env -- safe here since
        # this only ever touches the throwaway test database.
        call_command("seed_dev_data", "--force")

    def test_crawl_finds_no_broken_links(self):
        requested = os.environ.get("CRAWL_LOCALES")
        locales = (
            [code.strip() for code in requested.split(",") if code.strip()]
            if requested
            else [code for code, _name in settings.LANGUAGES]
        )
        for locale in locales:
            with self.subTest(locale=locale):
                self._crawl_locale(locale)

    def _crawl_locale(self, locale):
        """Crawl everything reachable from /<locale>/. The language switcher
        is a POST form, not a link, so an href into another locale's prefix
        means a page-link tag resolved to the wrong locale's page."""
        client = Client()
        other_prefixes = tuple(
            f"/{code}/" for code, _name in settings.LANGUAGES if code != locale
        )
        # href -> page it was first discovered on, for actionable failures.
        to_visit = {f"/{locale}/": "(start)"}
        visited = set()
        broken = []

        while to_visit and len(visited) < self.MAX_PAGES:
            url, source = to_visit.popitem()
            if url in visited:
                continue
            visited.add(url)

            try:
                response = client.get(url, follow=True)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                # A render/view crash is exactly the kind of thing this test
                # exists to catch -- record it and keep crawling instead of
                # letting one broken page hide every other result.
                broken.append(
                    f"{url!r} (linked from {source}) -> "
                    f"{exc.__class__.__name__}: {exc}"
                )
                continue

            if response.status_code != 200:
                broken.append(
                    f"{url!r} (linked from {source}) -> HTTP {response.status_code}"
                )
                continue

            html = response.content.decode("utf-8", errors="replace")
            for href in self.HREF_RE.findall(html):
                if href == "None":
                    broken.append(
                        f'href="None" found on {url!r} '
                        "(a page-link tag resolved to no URL)"
                    )
                    continue
                if not href.startswith("/") or href.startswith(self.EXCLUDED_PREFIXES):
                    continue
                if href.startswith(other_prefixes):
                    broken.append(
                        f"{href!r} found on {url!r} leads out of {locale!r} "
                        "into another locale"
                    )
                    continue
                if href not in visited and href not in to_visit:
                    to_visit[href] = url

        self.assertLess(
            len(visited),
            self.MAX_PAGES,
            f"{locale!r} crawl hit MAX_PAGES -- either the site legitimately "
            "grew this large (raise the cap) or something is generating a "
            "link cycle.",
        )

        if broken:
            details = "\n".join(f"  - {b}" for b in broken)
            self.fail(f"Found {len(broken)} broken link(s) in {locale!r}:\n{details}")
