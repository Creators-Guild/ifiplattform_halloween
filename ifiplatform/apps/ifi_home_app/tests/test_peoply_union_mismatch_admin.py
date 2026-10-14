# pylint: disable=C0114,C0115,C0116
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from wagtail.models import Locale, Page

from ifi_home_app.models.article.unions import StudentUnionCategoryPage, UnionPage
from ifi_home_app.models.event.peoply import PeoplyUnionMismatch

User = get_user_model()

ACTION = "create_union_pages_for_missing_orgs"
LINK_ACTION = "link_selected_unions"


def _make_union(**kwargs):
    root = Page.get_first_root_node()
    nb_locale, _ = Locale.objects.get_or_create(language_code="nb")
    kwargs.setdefault("title", "CYB")
    kwargs.setdefault("slug", "cyb")
    kwargs.setdefault("locale", nb_locale)
    union = UnionPage(**kwargs)
    root.add_child(instance=union)
    union.save_revision().publish()
    return union


def _make_union_category(**kwargs):
    root = Page.get_first_root_node()
    nb_locale, _ = Locale.objects.get_or_create(language_code="nb")
    kwargs.setdefault("title", "Studentforeninger")
    kwargs.setdefault("slug", "studentforeninger")
    kwargs.setdefault("locale", nb_locale)
    category = StudentUnionCategoryPage(**kwargs)
    root.add_child(instance=category)
    category.save_revision().publish()
    return category


def _make_mismatch(**kwargs):
    kwargs.setdefault("kind", "missing_org")
    kwargs.setdefault("identifier", "org-1")
    kwargs.setdefault("label", "New Org (neworg)")
    return PeoplyUnionMismatch.objects.create(**kwargs)


class CreateUnionPagesForMissingOrgsActionTests(TestCase):
    """PeoplyOrgsWithoutUnionAdmin's create_union_pages_for_missing_orgs
    bulk action -- the admin-side equivalent of check_peoply_union_matches
    --create-missing, for a superuser working from the mismatch log rather
    than a shell. Only registered on this one of the three PeoplyUnionMismatch
    proxy admins (models/event/peoply.py) -- creating a stub only makes sense in
    the "Peoply org with no site union" direction."""

    def setUp(self):
        Locale.objects.get_or_create(language_code="nb")
        self.superuser = User.objects.create_superuser("admin", "admin@test.com", "pw")
        self.client.force_login(self.superuser)
        self.changelist_url = reverse(
            "admin:ifi_home_app_peoplyorgswithoutunion_changelist"
        )

    def _post_action(self, mismatches):
        return self.client.post(
            self.changelist_url,
            {
                "action": ACTION,
                "_selected_action": [str(m.pk) for m in mismatches],
            },
            follow=True,
        )

    @patch("ifi_home_app.admin.get_organizations")
    def test_creates_draft_union_page_and_resolves_mismatch(self, mock_get_orgs):
        category = _make_union_category()
        mock_get_orgs.return_value = [
            {
                "id": "org-1",
                "name": "New Org",
                "urlId": "neworg",
                "websiteUrl": "https://neworg.example",
            }
        ]
        mismatch = _make_mismatch()

        response = self._post_action([mismatch])

        self.assertEqual(response.status_code, 200)
        stub = UnionPage.objects.get(title="New Org")
        self.assertEqual(stub.get_parent().specific, category)
        self.assertEqual(stub.peoply_organization_id, "org-1")
        self.assertEqual(stub.website_url, "https://neworg.example")
        self.assertFalse(stub.live)

        mismatch.refresh_from_db()
        self.assertIsNotNone(mismatch.resolved_at)

    @patch("ifi_home_app.admin.get_organizations")
    def test_non_superuser_is_refused(self, mock_get_orgs):
        _make_union_category()
        mock_get_orgs.return_value = [
            {"id": "org-1", "name": "New Org", "urlId": "neworg", "websiteUrl": None}
        ]
        staff_user = User.objects.create_user(
            "staff", "staff@test.com", "pw", is_staff=True
        )
        staff_user.is_superuser = False
        staff_user.save()
        self.client.force_login(staff_user)
        mismatch = _make_mismatch()

        # A non-superuser can't even reach the changelist (has_module/
        # view_permission gate on that), so the action never gets a
        # chance to run against real data.
        response = self.client.post(
            self.changelist_url,
            {
                "action": ACTION,
                "_selected_action": [str(mismatch.pk)],
            },
        )

        self.assertNotEqual(response.status_code, 200)
        self.assertFalse(UnionPage.objects.filter(title="New Org").exists())
        mismatch.refresh_from_db()
        self.assertIsNone(mismatch.resolved_at)

    @patch("ifi_home_app.admin.get_organizations")
    def test_org_no_longer_on_peoply_is_skipped_not_resolved(self, mock_get_orgs):
        _make_union_category()
        mock_get_orgs.return_value = (
            []
        )  # org-1 vanished from Peoply since it was flagged
        mismatch = _make_mismatch()

        self._post_action([mismatch])

        self.assertFalse(
            UnionPage.objects.filter(peoply_organization_id="org-1").exists()
        )
        mismatch.refresh_from_db()
        self.assertIsNone(mismatch.resolved_at)

    @patch("ifi_home_app.admin.get_organizations")
    def test_without_a_sole_category_nothing_is_created(self, mock_get_orgs):
        # No StudentUnionCategoryPage created at all -- ambiguous parent.
        mock_get_orgs.return_value = [
            {"id": "org-1", "name": "New Org", "urlId": "neworg", "websiteUrl": None}
        ]
        mismatch = _make_mismatch()

        self._post_action([mismatch])

        self.assertFalse(UnionPage.objects.filter(title="New Org").exists())
        mismatch.refresh_from_db()
        self.assertIsNone(mismatch.resolved_at)

    @patch("ifi_home_app.admin.get_organizations")
    def test_already_resolved_mismatch_is_skipped(self, mock_get_orgs):
        _make_union_category()
        mock_get_orgs.return_value = [
            {"id": "org-1", "name": "New Org", "urlId": "neworg", "websiteUrl": None}
        ]
        mismatch = _make_mismatch(resolved_at=timezone.now())

        self._post_action([mismatch])

        self.assertFalse(UnionPage.objects.filter(title="New Org").exists())


class LinkSelectedUnionsActionTests(TestCase):
    """UnionsPendingPeoplyLinkAdmin's link_selected_unions bulk action --
    the admin-side equivalent of link_peoply_organizations --apply, for a
    superuser working from the mismatch log rather than a shell."""

    def setUp(self):
        Locale.objects.get_or_create(language_code="nb")
        self.superuser = User.objects.create_superuser("admin", "admin@test.com", "pw")
        self.client.force_login(self.superuser)
        self.changelist_url = reverse(
            "admin:ifi_home_app_unionspendingpeoplylink_changelist"
        )

    def _post_action(self, mismatches):
        return self.client.post(
            self.changelist_url,
            {
                "action": LINK_ACTION,
                "_selected_action": [str(m.pk) for m in mismatches],
            },
            follow=True,
        )

    def _make_pending_mismatch(self, union, **kwargs):
        kwargs.setdefault("kind", "pending_link")
        kwargs.setdefault("identifier", str(union.translation_key))
        kwargs.setdefault("label", f"{union.title} -> CYB (cyb)")
        return PeoplyUnionMismatch.objects.create(**kwargs)

    @patch("ifi_home_app.admin.get_organizations")
    def test_links_union_and_resolves_mismatch(self, mock_get_orgs):
        union = _make_union()
        mock_get_orgs.return_value = [
            {"id": "org-1", "name": "CYB", "urlId": "cyb", "websiteUrl": None}
        ]
        mismatch = self._make_pending_mismatch(union)

        response = self._post_action([mismatch])

        self.assertEqual(response.status_code, 200)
        union.refresh_from_db()
        self.assertEqual(union.peoply_organization_id, "org-1")

        mismatch.refresh_from_db()
        self.assertIsNotNone(mismatch.resolved_at)

    @patch("ifi_home_app.admin.get_organizations")
    def test_non_superuser_is_refused(self, mock_get_orgs):
        union = _make_union()
        mock_get_orgs.return_value = [
            {"id": "org-1", "name": "CYB", "urlId": "cyb", "websiteUrl": None}
        ]
        staff_user = User.objects.create_user(
            "staff", "staff@test.com", "pw", is_staff=True
        )
        staff_user.is_superuser = False
        staff_user.save()
        self.client.force_login(staff_user)
        mismatch = self._make_pending_mismatch(union)

        response = self.client.post(
            self.changelist_url,
            {
                "action": LINK_ACTION,
                "_selected_action": [str(mismatch.pk)],
            },
        )

        self.assertNotEqual(response.status_code, 200)
        union.refresh_from_db()
        self.assertEqual(union.peoply_organization_id, "")
        mismatch.refresh_from_db()
        self.assertIsNone(mismatch.resolved_at)

    @patch("ifi_home_app.admin.get_organizations")
    def test_match_no_longer_exact_is_skipped_not_resolved(self, mock_get_orgs):
        union = _make_union()
        # org-1 renamed on Peoply's side since the mismatch was flagged --
        # title no longer matches exactly.
        mock_get_orgs.return_value = [
            {
                "id": "org-1",
                "name": "Something Else",
                "urlId": "else",
                "websiteUrl": None,
            }
        ]
        mismatch = self._make_pending_mismatch(union)

        self._post_action([mismatch])

        union.refresh_from_db()
        self.assertEqual(union.peoply_organization_id, "")
        mismatch.refresh_from_db()
        self.assertIsNone(mismatch.resolved_at)

    @patch("ifi_home_app.admin.get_organizations")
    def test_already_resolved_mismatch_is_skipped(self, mock_get_orgs):
        union = _make_union()
        mock_get_orgs.return_value = [
            {"id": "org-1", "name": "CYB", "urlId": "cyb", "websiteUrl": None}
        ]
        mismatch = self._make_pending_mismatch(union, resolved_at=timezone.now())

        self._post_action([mismatch])

        union.refresh_from_db()
        self.assertEqual(union.peoply_organization_id, "")


class MismatchProxyListingIsolationTests(TestCase):
    """The four PeoplyUnionMismatch proxy admins (models/event/peoply.py) each
    read as a separate log -- confirms one kind's rows never leak into
    another proxy's changelist, which is the whole point of splitting them
    up instead of one combined filterable list."""

    def setUp(self):
        self.superuser = User.objects.create_superuser("admin", "admin@test.com", "pw")
        self.client.force_login(self.superuser)
        _make_mismatch(kind="unlinked_union", identifier="u-1", label="Unlinked Union")
        _make_mismatch(
            kind="stale_link", identifier="u-2", label="Stale Union (bad-id)"
        )
        _make_mismatch(kind="missing_org", identifier="org-1", label="Missing Org")
        _make_mismatch(
            kind="pending_link", identifier="u-3", label="Pending Union (found match)"
        )

    def test_each_proxy_shows_only_its_own_kind(self):
        cases = [
            ("ifi_home_app_unionswithoutpeoplyorg_changelist", "Unlinked Union"),
            (
                "ifi_home_app_unionswithstalepeoplylink_changelist",
                "Stale Union (bad-id)",
            ),
            ("ifi_home_app_peoplyorgswithoutunion_changelist", "Missing Org"),
            (
                "ifi_home_app_unionspendingpeoplylink_changelist",
                "Pending Union (found match)",
            ),
        ]
        all_labels = {
            "Unlinked Union",
            "Stale Union (bad-id)",
            "Missing Org",
            "Pending Union (found match)",
        }

        for url_name, expected_label in cases:
            response = self.client.get(reverse(f"admin:{url_name}"))
            content = response.content.decode()
            self.assertIn(expected_label, content)
            for other_label in all_labels - {expected_label}:
                self.assertNotIn(other_label, content)
