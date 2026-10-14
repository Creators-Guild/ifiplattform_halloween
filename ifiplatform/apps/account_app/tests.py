# pylint: disable=C0114,C0115,C0116
import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone, translation

from wagtail.models import GroupPagePermission, Page

from account_app.models import Profile
from ifi_home_app.models import ArticlePage
from study_app.models import Card, Deck

User = get_user_model()


def _make_article(author=None, **kwargs):
    """A minimal ArticlePage, saved directly under the site root -- bypasses
    ArticlePage.parent_page_types (an admin-UI-only restriction, not
    enforced by add_child()) since these tests only care about the
    author/attribution fields, not the real category tree."""
    root = Page.get_first_root_node()
    kwargs.setdefault("title", "Test Article")
    kwargs.setdefault("slug", "test-article")
    kwargs.setdefault("published_date", timezone.now().date())
    article = ArticlePage(body=[], author=author, **kwargs)
    root.add_child(instance=article)
    return article


class DisplayAuthorNameTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", password="pw", first_name="Alice", last_name="Anderson"
        )

    def test_author_present_real_name(self):
        article = ArticlePage(author=self.user, author_attribution="real_name")
        self.assertEqual(article.display_author_name, "Alice Anderson")

    def test_author_present_nickname(self):
        Profile.objects.create(user=self.user, nickname="Al")
        article = ArticlePage(author=self.user, author_attribution="nickname")
        self.assertEqual(article.display_author_name, "Al")

    def test_author_present_nickname_attribution_but_no_nickname_set(self):
        article = ArticlePage(author=self.user, author_attribution="nickname")
        self.assertEqual(article.display_author_name, "Alice Anderson")

    def test_author_gone_real_name_snapshot(self):
        article = ArticlePage(author_display_name="Alice Anderson")
        self.assertEqual(article.display_author_name, "Alice Anderson")

    def test_author_gone_nickname_snapshot(self):
        article = ArticlePage(author_display_name="Al")
        self.assertEqual(article.display_author_name, "Al")

    def test_author_gone_unknown_sentinel(self):
        article = ArticlePage(author_display_name="unknown")
        with translation.override("en"):
            self.assertEqual(article.display_author_name, "Unknown")

    def test_never_had_author(self):
        article = ArticlePage()
        self.assertIsNone(article.display_author_name)


class AccountDeletionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="bob", password="pw", first_name="Bob", last_name="Builder"
        )
        self.profile = Profile.objects.create(user=self.user, nickname="Bobby")
        self.deck = Deck.objects.create(owner=self.user, name="My Deck")
        Card.objects.create(deck=self.deck, front="Q", back="A")
        self.article = _make_article(author=self.user, slug="bobs-article")
        self.client.login(username="bob", password="pw")

    def test_wrong_password_rejected(self):
        response = self.client.post(
            reverse("delete_account"),
            {
                "password": "wrong",
                "study_tools_action": "delete",
                "articles_attribution": "unknown",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())
        self.assertTrue(Deck.objects.filter(pk=self.deck.pk).exists())

    def test_delete_studytools_unknown_articles(self):
        response = self.client.post(
            reverse("delete_account"),
            {
                "password": "pw",
                "study_tools_action": "delete",
                "articles_attribution": "unknown",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        self.assertFalse(Deck.objects.filter(pk=self.deck.pk).exists())
        self.article.refresh_from_db()
        self.assertIsNone(self.article.author_id)
        self.assertEqual(self.article.author_display_name, "unknown")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_keep_studytools_nickname_without_nickname_rejected(self):
        other = User.objects.create_user(username="carol", password="pw")
        self.client.login(username="carol", password="pw")
        response = self.client.post(
            reverse("delete_account"),
            {
                "password": "pw",
                "study_tools_action": "keep",
                "study_tools_attribution": "nickname",
                "articles_attribution": "real_name",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(pk=other.pk).exists())

    def test_keep_studytools_nickname_articles_real_name(self):
        response = self.client.post(
            reverse("delete_account"),
            {
                "password": "pw",
                "study_tools_action": "keep",
                "study_tools_attribution": "nickname",
                "articles_attribution": "real_name",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())

        self.deck.refresh_from_db()
        self.assertIsNone(self.deck.owner_id)
        self.assertEqual(self.deck.owner_display_name, "Bobby")

        self.article.refresh_from_db()
        self.assertIsNone(self.article.author_id)
        self.assertEqual(self.article.author_display_name, "Bob Builder")


class ExportDataTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dana", password="pw", first_name="Dana", last_name="Diaz"
        )
        Profile.objects.create(user=self.user, nickname="D")
        self.deck = Deck.objects.create(owner=self.user, name="Export Deck")
        Card.objects.create(deck=self.deck, front="Q1", back="A1")
        _make_article(author=self.user, slug="danas-article", title="Dana's Article")

    def test_requires_login(self):
        response = self.client.get(reverse("export_data"))
        self.assertNotEqual(response.status_code, 200)

    def test_export_contains_expected_fields(self):
        self.client.login(username="dana", password="pw")
        response = self.client.get(reverse("export_data"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = json.loads(response.content)
        self.assertEqual(data["username"], "dana")
        self.assertEqual(data["nickname"], "D")
        self.assertEqual(data["decks"][0]["name"], "Export Deck")
        self.assertEqual(data["decks"][0]["cards"][0]["front"], "Q1")
        self.assertEqual(data["authored_articles"][0]["title"], "Dana's Article")


class EditorNoticeTests(TestCase):
    def setUp(self):
        self.root = Page.get_first_root_node()
        # "Editors"/"Moderators" already exist as Wagtail's own built-in
        # groups (from its own data migration) -- distinct names here to
        # avoid colliding with those.
        self.editor_group = Group.objects.create(name="Test Article Writers")
        GroupPagePermission.objects.create(
            group=self.editor_group, page=self.root, permission_type="add"
        )
        self.other_group = Group.objects.create(name="Test Newsletter")

    def test_non_admin_editor_sees_notice(self):
        user = User.objects.create_user(username="eve", password="pw")
        user.groups.add(self.editor_group)
        self.client.login(username="eve", password="pw")
        response = self.client.get(reverse("account_settings"))
        self.assertTrue(response.context["show_editor_notice"])

    def test_agree_hides_notice(self):
        user = User.objects.create_user(username="frank", password="pw")
        user.groups.add(self.editor_group)
        self.client.login(username="frank", password="pw")
        self.client.post(reverse("editor_terms_response"), {"decision": "agree"})
        user.refresh_from_db()
        self.assertEqual(user.profile.editor_terms_status, "agreed")
        response = self.client.get(reverse("account_settings"))
        self.assertFalse(response.context["show_editor_notice"])

    def test_disagree_removes_only_editor_group(self):
        user = User.objects.create_user(username="gina", password="pw")
        user.groups.add(self.editor_group, self.other_group)
        self.client.login(username="gina", password="pw")
        self.client.post(reverse("editor_terms_response"), {"decision": "disagree"})
        user.refresh_from_db()
        self.assertEqual(user.profile.editor_terms_status, "disagreed")
        self.assertNotIn(self.editor_group, user.groups.all())
        self.assertIn(self.other_group, user.groups.all())

    def test_admin_never_sees_notice(self):
        admin = User.objects.create_user(username="henry", password="pw", is_staff=True)
        admin.groups.add(self.editor_group)
        self.client.login(username="henry", password="pw")
        response = self.client.get(reverse("account_settings"))
        self.assertFalse(response.context["show_editor_notice"])


class WagtailBuiltinGroupsTests(TestCase):
    """is_pending_editor() is a permission check (add_page/change_page),
    not a check against a specific group name -- so it applies equally to
    Wagtail's own built-in "Moderators" group (add/change/publish/lock/
    unlock, confirmed against the real dev DB), not just "Editors"
    (add/change only), and to a user who happens to be in both at once
    (e.g. added to Moderators without ever being in Editors first, or added
    to both by mistake). Both groups already exist from Wagtail's own data
    migration -- looked up by name rather than created here."""

    def setUp(self):
        self.editors_group = Group.objects.get(name="Editors")
        self.moderators_group = Group.objects.get(name="Moderators")

    def test_moderator_only_sees_notice_and_is_gated(self):
        user = User.objects.create_user(username="mod_only", password="pw")
        user.groups.add(self.moderators_group)
        self.client.login(username="mod_only", password="pw")

        settings_response = self.client.get(reverse("account_settings"))
        self.assertTrue(settings_response.context["show_editor_notice"])

        admin_response = self.client.get(reverse("wagtailadmin_home"))
        self.assertRedirects(
            admin_response, reverse("account_settings") + "?editor_terms=required"
        )

    def test_moderator_only_agree_unblocks_wagtail_admin(self):
        user = User.objects.create_user(username="mod_agree", password="pw")
        user.groups.add(self.moderators_group)
        self.client.login(username="mod_agree", password="pw")
        self.client.post(reverse("editor_terms_response"), {"decision": "agree"})
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)

    def test_editor_and_moderator_at_once_sees_notice(self):
        user = User.objects.create_user(username="both_pending", password="pw")
        user.groups.add(self.editors_group, self.moderators_group)
        self.client.login(username="both_pending", password="pw")
        response = self.client.get(reverse("account_settings"))
        self.assertTrue(response.context["show_editor_notice"])

    def test_editor_and_moderator_at_once_disagree_removes_both(self):
        user = User.objects.create_user(username="both_disagree", password="pw")
        user.groups.add(self.editors_group, self.moderators_group)
        self.client.login(username="both_disagree", password="pw")
        self.client.post(reverse("editor_terms_response"), {"decision": "disagree"})
        user.refresh_from_db()
        self.assertEqual(user.profile.editor_terms_status, "disagreed")
        remaining = set(user.groups.values_list("name", flat=True))
        self.assertNotIn("Editors", remaining)
        self.assertNotIn("Moderators", remaining)

    def test_editor_and_moderator_at_once_agree_unblocks_wagtail_admin(self):
        user = User.objects.create_user(username="both_agree", password="pw")
        user.groups.add(self.editors_group, self.moderators_group)
        self.client.login(username="both_agree", password="pw")
        self.client.post(reverse("editor_terms_response"), {"decision": "agree"})
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)
        # still in both groups -- agreeing only records the decision, it
        # never touches group membership (only disagreeing does).
        remaining = set(user.groups.values_list("name", flat=True))
        self.assertIn("Editors", remaining)
        self.assertIn("Moderators", remaining)


class IndividualUserPermissionsTests(TestCase):
    """Wagtail's own page-permission system (page_permission_policy,
    Page.permissions_for_user()) only ever looks at GroupPagePermission --
    tied to a Group and a specific page in the tree -- never at Django's
    generic per-user Permission assignment (the "Brukerrettigheter"/"User
    permissions" widget on the Django admin user-change form). Confirmed
    empirically against this exact Wagtail version: a user given add_page/
    change_page directly (no group at all) has user.has_perm(...)==True,
    but page_permission_policy/can_edit() are still False everywhere, so
    they can't actually create or edit a single page. is_pending_editor()
    and can_edit_in_editor_mode() both key off that same page-permission
    check, not off has_perm() -- so this route grants no real editing
    capability to gate in the first place, and can't be used to bypass the
    content-ownership terms. This test exists so a future Wagtail upgrade
    that ever changed that behavior wouldn't do so silently."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="direct_perms_only", password="pw"
        )
        self.user.user_permissions.add(
            Permission.objects.get(
                codename="add_page", content_type__app_label="wagtailcore"
            ),
            Permission.objects.get(
                codename="change_page", content_type__app_label="wagtailcore"
            ),
        )

    def test_direct_permissions_grant_no_real_page_permission(self):
        self.assertTrue(self.user.has_perm("wagtailcore.add_page"))
        self.assertTrue(self.user.has_perm("wagtailcore.change_page"))
        root = Page.get_first_root_node()
        self.assertFalse(root.permissions_for_user(self.user).can_edit())

    def test_direct_permissions_do_not_trigger_the_terms_notice(self):
        # Nothing to gate: is_pending_editor is False here not because the
        # user is exempt, but because they have no real editing capability
        # for the notice to be about in the first place.
        self.client.login(username="direct_perms_only", password="pw")
        response = self.client.get(reverse("account_settings"))
        self.assertFalse(response.context["show_editor_notice"])


class EditorTermsGateMiddlewareTests(TestCase):
    """Covers the actual enforcement point (see EditorTermsGateMiddleware's
    own docstring for why account_settings_view's notice alone isn't
    enough): a pending editor must be stopped at the door of /wagtail-admin/
    itself, not just shown a notice they could simply never visit."""

    def setUp(self):
        self.root = Page.get_first_root_node()
        self.editor_group = Group.objects.create(name="Test Middleware Writers")
        GroupPagePermission.objects.create(
            group=self.editor_group, page=self.root, permission_type="add"
        )
        # Wagtail's own admin login gate needs this Django permission
        # (separate from GroupPagePermission) to let a request past its own
        # login check at all -- Wagtail's built-in "Editors"/"Moderators"
        # groups already bundle it (confirmed against the real dev DB), so
        # this custom test group needs it added explicitly to match.
        self.editor_group.permissions.add(
            Permission.objects.get(
                codename="access_admin", content_type__app_label="wagtailadmin"
            )
        )
        self.wagtail_admin_url = reverse("wagtailadmin_home")

    def test_pending_editor_redirected_to_account_settings(self):
        user = User.objects.create_user(username="ivy", password="pw")
        user.groups.add(self.editor_group)
        self.client.login(username="ivy", password="pw")
        response = self.client.get(self.wagtail_admin_url)
        expected_url = reverse("account_settings") + "?editor_terms=required"
        self.assertRedirects(response, expected_url)

    def test_pending_editor_redirect_shakes_the_terms_box(self):
        # ?editor_terms=required (set only by this middleware's own
        # redirect) is what account_settings_view reads to shake the terms
        # box -- see the plain self-navigated case just below, which must
        # NOT shake.
        user = User.objects.create_user(username="ivy2", password="pw")
        user.groups.add(self.editor_group)
        self.client.login(username="ivy2", password="pw")
        redirect_response = self.client.get(self.wagtail_admin_url)
        settings_response = self.client.get(redirect_response.url)
        self.assertTrue(settings_response.context["editor_terms_shake"])

    def test_direct_visit_to_account_settings_does_not_shake(self):
        user = User.objects.create_user(username="ivy3", password="pw")
        user.groups.add(self.editor_group)
        self.client.login(username="ivy3", password="pw")
        response = self.client.get(reverse("account_settings"))
        self.assertFalse(response.context["editor_terms_shake"])

    def test_agreed_editor_reaches_wagtail_admin(self):
        user = User.objects.create_user(username="jack", password="pw")
        user.groups.add(self.editor_group)
        Profile.objects.create(user=user, editor_terms_status="agreed")
        self.client.login(username="jack", password="pw")
        response = self.client.get(self.wagtail_admin_url)
        self.assertEqual(response.status_code, 200)

    def test_admin_reaches_wagtail_admin_regardless_of_status(self):
        admin = User.objects.create_user(username="kim", password="pw", is_staff=True)
        admin.groups.add(self.editor_group)
        self.client.login(username="kim", password="pw")
        response = self.client.get(self.wagtail_admin_url)
        self.assertEqual(response.status_code, 200)

    def test_non_editor_not_redirected_by_this_middleware(self):
        # Not in editor_group at all, so no page permission and no
        # wagtailadmin.access_admin -- Wagtail's own admin login gate will
        # still redirect them somewhere (its own login screen), which is
        # correct and none of this middleware's business; what matters here
        # is only that it's not *this* middleware sending them to
        # account_settings.
        user = User.objects.create_user(username="liam", password="pw")
        self.client.login(username="liam", password="pw")
        response = self.client.get(self.wagtail_admin_url)
        if response.status_code == 302:
            self.assertNotEqual(response.url, reverse("account_settings"))


class CleanupUnverifiedAccountsTests(TestCase):
    def _make_unverified(self, username, days_old):
        user = User.objects.create_user(
            username=username, password="pw", is_active=False
        )
        User.objects.filter(pk=user.pk).update(
            date_joined=timezone.now() - timezone.timedelta(days=days_old)
        )
        return user

    def test_deletes_old_unverified(self):
        user = self._make_unverified("old_unverified", 10)
        call_command("cleanup_unverified_accounts")
        self.assertFalse(User.objects.filter(pk=user.pk).exists())

    def test_keeps_recent_unverified(self):
        user = self._make_unverified("recent_unverified", 1)
        call_command("cleanup_unverified_accounts")
        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_keeps_active_regardless_of_age(self):
        user = User.objects.create_user(
            username="old_active", password="pw", is_active=True
        )
        User.objects.filter(pk=user.pk).update(
            date_joined=timezone.now() - timezone.timedelta(days=30)
        )
        call_command("cleanup_unverified_accounts")
        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_dry_run_deletes_nothing(self):
        user = self._make_unverified("dry_run_unverified", 10)
        call_command("cleanup_unverified_accounts", "--dry-run")
        self.assertTrue(User.objects.filter(pk=user.pk).exists())
