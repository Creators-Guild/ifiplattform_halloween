# pylint: disable=C0114,C0115,C0116
import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from wagtail.models import GroupPagePermission, Page

from account_app.models import Profile
from ifi_home_app.models import ArticlePage
from ifi_home_app.models.article_models import CategoryPage

User = get_user_model()


def _make_article(**kwargs):
    """Mirrors account_app.tests._make_article -- a minimal ArticlePage
    saved directly under the site root, bypassing parent_page_types (an
    admin-UI-only restriction, not enforced by add_child())."""
    root = Page.get_first_root_node()
    kwargs.setdefault("title", "Test Article")
    kwargs.setdefault("slug", "test-article")
    kwargs.setdefault("published_date", timezone.now().date())
    article = ArticlePage(body=[], **kwargs)
    root.add_child(instance=article)
    return article


def _make_category(**kwargs):
    root = Page.get_first_root_node()
    kwargs.setdefault("title", "Test Category")
    kwargs.setdefault("slug", "test-category")
    category = CategoryPage(**kwargs)
    root.add_child(instance=category)
    return category


class EditorModeMixinTests(TestCase):
    """Unit-level coverage of the shared rule itself (EditorModeMixin.
    can_edit_in_editor_mode / ArticlePage.can_publish_in_editor_mode /
    can_unpublish_in_editor_mode) -- see account_app.tests.EditorNoticeTests/
    EditorTermsGateMiddlewareTests for the equivalent wagtail-admin-side
    coverage."""

    def setUp(self):
        self.root = Page.get_first_root_node()
        self.editor_group = Group.objects.create(name="Test Editor Mode Writers")
        # "add" alone only lets a user edit pages *they themselves created*
        # (Page.owner) -- these test pages have no owner, so "change" is
        # needed too for can_edit() to be True, matching Wagtail's own
        # built-in Editors group (confirmed against the real dev DB: it
        # carries both add_page and change_page).
        for permission_type in ("add", "change", "publish"):
            GroupPagePermission.objects.create(
                group=self.editor_group, page=self.root, permission_type=permission_type
            )
        self.article = _make_article()

    def _make_user(self, username, *, agreed=False, is_staff=False):
        user = User.objects.create_user(
            username=username, password="pw", is_staff=is_staff
        )
        user.groups.add(self.editor_group)
        Profile.objects.create(
            user=user, editor_terms_status="agreed" if agreed else "pending"
        )
        return user

    def test_agreed_editor_can_edit(self):
        user = self._make_user("agreed_editor", agreed=True)
        self.assertTrue(self.article.can_edit_in_editor_mode(user))

    def test_pending_editor_cannot_edit(self):
        user = self._make_user("pending_editor", agreed=False)
        self.assertFalse(self.article.can_edit_in_editor_mode(user))

    def test_non_editor_cannot_edit_regardless_of_terms_status(self):
        user = User.objects.create_user(username="not_an_editor", password="pw")
        Profile.objects.create(user=user, editor_terms_status="agreed")
        self.assertFalse(self.article.can_edit_in_editor_mode(user))

    def test_admin_can_edit_regardless_of_terms_status(self):
        admin = self._make_user("admin_editor", agreed=False, is_staff=True)
        self.assertTrue(self.article.can_edit_in_editor_mode(admin))

    def test_agreed_editor_can_publish_and_unpublish(self):
        user = self._make_user("agreed_publisher", agreed=True)
        self.assertTrue(self.article.can_publish_in_editor_mode(user))
        self.assertTrue(self.article.can_unpublish_in_editor_mode(user))

    def test_pending_editor_cannot_publish_or_unpublish(self):
        user = self._make_user("pending_publisher", agreed=False)
        self.assertFalse(self.article.can_publish_in_editor_mode(user))
        self.assertFalse(self.article.can_unpublish_in_editor_mode(user))


class EditorModeEndpointTests(TestCase):
    """HTTP-level regression coverage confirming the terms-gate actually
    reaches the real save endpoints, not just the underlying mixin method.
    save_quick_style is used as the representative for save_block_style/
    save_header_style/save_hero_image_style/save_toc_icon_style too -- all
    five now share byte-identical permission-check code
    (`page.can_edit_in_editor_mode(request.user)`), so this isn't gold-
    plated coverage of five near-duplicate call sites; publish_page/
    unpublish_page and save_banner_style are covered separately since they
    exercise different mixin methods and (for banner) a different page
    type."""

    def setUp(self):
        self.root = Page.get_first_root_node()
        self.editor_group = Group.objects.create(name="Test Endpoint Writers")
        for permission_type in ("add", "change", "publish"):
            GroupPagePermission.objects.create(
                group=self.editor_group, page=self.root, permission_type=permission_type
            )
        self.article = _make_article()
        self.category = _make_category()

    def _login_editor(self, username, *, agreed):
        user = User.objects.create_user(username=username, password="pw")
        user.groups.add(self.editor_group)
        Profile.objects.create(
            user=user, editor_terms_status="agreed" if agreed else "pending"
        )
        self.client.login(username=username, password="pw")
        return user

    def test_quick_style_blocked_while_pending(self):
        self._login_editor("quick_style_pending", agreed=False)
        response = self.client.post(
            reverse("article_quick_style", kwargs={"page_id": self.article.pk}),
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_quick_style_allowed_once_agreed(self):
        self._login_editor("quick_style_agreed", agreed=True)
        response = self.client.post(
            reverse("article_quick_style", kwargs={"page_id": self.article.pk}),
            data=json.dumps(
                {
                    "content_side_padding": 0,
                    "content_alignment": "left",
                    "content_font_size_multiplier": 1,
                    "content_bg_enabled": False,
                    "content_bg_color": "bg-light",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

    def test_publish_blocked_while_pending(self):
        self._login_editor("publisher_pending", agreed=False)
        response = self.client.post(
            reverse("article_publish", kwargs={"page_id": self.article.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_unpublish_blocked_while_pending(self):
        self._login_editor("unpublisher_pending", agreed=False)
        response = self.client.post(
            reverse("article_unpublish", kwargs={"page_id": self.article.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_publish_not_blocked_by_gate_once_agreed(self):
        # Not asserting 200 -- publish_page also requires an actual draft
        # revision to exist (unrelated business rule, returns 400 without
        # one). What matters here is only that the terms-gate itself no
        # longer produces a 403 once agreed.
        self._login_editor("publisher_agreed", agreed=True)
        response = self.client.post(
            reverse("article_publish", kwargs={"page_id": self.article.pk})
        )
        self.assertNotEqual(response.status_code, 403)

    def test_block_style_rejects_out_of_range_width(self):
        # width_rem/height_rem have no bound in the request body itself --
        # the on-page slider caps at 4-60rem/0-40rem (article_block_style_
        # mini_panel.html), but a direct POST bypasses that entirely. This
        # confirms the server-side bound added alongside the mobile-overflow
        # fix (article_multicolumn.css et al) actually rejects a value the
        # slider could never produce, same pattern as save_banner_style's
        # own width/height bound below.
        self._login_editor("block_style_oversized", agreed=True)
        response = self.client.post(
            reverse("article_block_style", kwargs={"page_id": self.article.pk}),
            data=json.dumps(
                {
                    "block_id": "test-block",
                    "block_type": "article_card",
                    "width_rem": 999,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_block_style_allows_in_range_width(self):
        self._login_editor("block_style_normal", agreed=True)
        response = self.client.post(
            reverse("article_block_style", kwargs={"page_id": self.article.pk}),
            data=json.dumps(
                {
                    "block_id": "test-block",
                    "block_type": "article_card",
                    "width_rem": 20,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

    def test_hero_image_style_rejects_out_of_range_width(self):
        self._login_editor("hero_image_oversized", agreed=True)
        response = self.client.post(
            reverse("article_hero_image_style", kwargs={"page_id": self.article.pk}),
            data=json.dumps(
                {
                    "alignment": "center",
                    "width_rem": 999,
                    "side_padding": 0,
                    "boxed": False,
                    "box_color": "",
                    "box_border_radius": 0,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_banner_style_blocked_while_pending(self):
        self._login_editor("banner_pending", agreed=False)
        response = self.client.post(
            reverse("page_banner_style", kwargs={"page_id": self.category.pk}),
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_banner_style_allowed_once_agreed(self):
        self._login_editor("banner_agreed", agreed=True)
        response = self.client.post(
            reverse("page_banner_style", kwargs={"page_id": self.category.pk}),
            data=json.dumps(
                {
                    "show_banner": False,
                    "banner_color": "",
                    "banner_dot_color": "",
                    "banner_text_color": "",
                    "banner_width_rem": None,
                    "banner_height_rem": None,
                    "banner_font_size": None,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)


class ArticlePageContextTests(TestCase):
    """Confirms get_context()'s can_edit_style/can_publish_page/
    can_unpublish_page reflect the terms-gate too -- the UI-visibility side
    of the fix, not just the write-endpoint side covered above. Uses
    RequestFactory + get_context() directly rather than a real GET of the
    page's own URL, since these test pages are created directly under the
    tree root (bypassing parent_page_types, see _make_article's own
    docstring) with no guarantee a Wagtail Site maps to that tree for
    routing purposes -- get_context() is the exact method whose behavior
    changed, so this tests it directly rather than through routing that has
    nothing to do with this fix."""

    def setUp(self):
        self.root = Page.get_first_root_node()
        self.editor_group = Group.objects.create(name="Test Context Writers")
        for permission_type in ("add", "change"):
            GroupPagePermission.objects.create(
                group=self.editor_group, page=self.root, permission_type=permission_type
            )
        self.article = _make_article()
        self.factory = RequestFactory()

    def _context_for(self, user):
        request = self.factory.get("/")
        request.user = user
        return self.article.get_context(request)

    def test_can_edit_style_false_while_pending(self):
        user = User.objects.create_user(username="context_pending", password="pw")
        user.groups.add(self.editor_group)
        Profile.objects.create(user=user, editor_terms_status="pending")
        self.assertFalse(self._context_for(user)["can_edit_style"])

    def test_can_edit_style_true_once_agreed(self):
        user = User.objects.create_user(username="context_agreed", password="pw")
        user.groups.add(self.editor_group)
        Profile.objects.create(user=user, editor_terms_status="agreed")
        self.assertTrue(self._context_for(user)["can_edit_style"])
