# pylint: disable=C0114,C0115,C0116
from datetime import datetime, timezone as dt_timezone
from io import StringIO
from unittest.mock import Mock, patch

import requests
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from wagtail.models import Locale, Page

from ifi_home_app.integrations.peoply_api import get_events
from ifi_home_app.models.article.unions import StudentUnionCategoryPage, UnionPage
from ifi_home_app.models.event.pages import EventIndexPage, EventPage
from ifi_home_app.models.event.peoply import (
    PeoplyRemovedEvent,
    PeoplyUnionMismatch,
)
from ifi_home_app.models.event.queries import upcoming_events_for_union

SAMPLE_EVENT = {
    "id": "d01f8be8-6bd0-40ff-850d-7e3ccc04d8f5",
    "urlId": "TNMRSSQR",
    "title": "Semesterstartfest",
    "description": "Line one.\r\nLine two.\r\n\r\nNew paragraph.",
    "startDate": "2026-01-16T19:00:00.000Z",  # 20:00 Europe/Oslo (CET, UTC+1 in January)
    "endDate": None,
    "locationName": "Escape",
    "freeformAddress": "Gaustadalléen 23B, 0373 Oslo",
}


def _fake_response(json_data, status_code=200):
    response = Mock()
    response.json.return_value = json_data
    response.status_code = status_code
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(
            f"{status_code} error"
        )
    return response


def _make_union(**kwargs):
    root = Page.get_first_root_node()
    nb_locale, _ = Locale.objects.get_or_create(language_code="nb")
    kwargs.setdefault("title", "Test Union")
    kwargs.setdefault("slug", "test-union")
    kwargs.setdefault("locale", nb_locale)
    union = UnionPage(**kwargs)
    root.add_child(instance=union)
    union.save_revision().publish()
    return union


def _make_event_index(**kwargs):
    root = Page.get_first_root_node()
    nb_locale, _ = Locale.objects.get_or_create(language_code="nb")
    kwargs.setdefault("title", "Events")
    kwargs.setdefault("slug", "events")
    kwargs.setdefault("locale", nb_locale)
    index = EventIndexPage(**kwargs)
    root.add_child(instance=index)
    index.save_revision().publish()
    return index


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


def _fake_org(**kwargs):
    kwargs.setdefault("id", "org-id")
    kwargs.setdefault("name", "Test Org")
    kwargs.setdefault("urlId", "testorg")
    kwargs.setdefault("websiteUrl", None)
    return kwargs


class GetEventsTests(TestCase):
    """peoply_api.get_events's pagination stitching and error handling."""

    @patch("ifi_home_app.integrations.peoply_api.requests.get")
    def test_stitches_multiple_pages(self, mock_get):
        full_page = [{"id": i} for i in range(500)]
        last_page = [{"id": 500}]
        mock_get.side_effect = [_fake_response(full_page), _fake_response(last_page)]

        events = get_events("union-id", datetime.now(dt_timezone.utc))

        self.assertEqual(len(events), 501)
        self.assertEqual(mock_get.call_count, 2)

    @patch("ifi_home_app.integrations.peoply_api.requests.get")
    def test_single_short_page_stops_immediately(self, mock_get):
        mock_get.side_effect = [_fake_response([{"id": 1}])]

        events = get_events("union-id", datetime.now(dt_timezone.utc))

        self.assertEqual(len(events), 1)
        self.assertEqual(mock_get.call_count, 1)

    @patch("ifi_home_app.integrations.peoply_api.requests.get")
    def test_raises_on_error_response(self, mock_get):
        mock_get.return_value = _fake_response([], status_code=500)

        with self.assertRaises(requests.HTTPError):
            get_events("union-id", datetime.now(dt_timezone.utc))


class SyncPeoplyEventsTests(TestCase):
    """The sync_peoply_events management command."""

    def setUp(self):
        self.union = _make_union(peoply_organization_id="test-org-id")
        self.event_index = _make_event_index()
        # sync_peoply_events runs check_peoply_union_matches automatically
        # at the end of every sync (see that command's own docstring) --
        # stub its organizations fetch so these tests don't hit the real
        # Peoply API just to exercise event syncing.
        patcher = patch(
            "ifi_home_app.management.commands.check_peoply_union_matches.get_organizations",
            return_value=[],
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    @patch("ifi_home_app.management.commands.sync_peoply_events.get_events")
    def test_creates_event_page_with_expected_fields(self, mock_get_events):
        mock_get_events.return_value = [SAMPLE_EVENT]

        call_command("sync_peoply_events")

        page = EventPage.objects.get(
            external_source="peoply", external_uid=SAMPLE_EVENT["id"]
        )
        self.assertEqual(page.title, "Semesterstartfest")
        self.assertEqual(page.get_parent().specific, self.event_index)
        self.assertTrue(page.live)
        self.assertEqual(page.event_type, "social")
        self.assertEqual(page.peoply_url, "https://peoply.app/events/TNMRSSQR")
        self.assertEqual(page.location, "Gaustadalléen 23B, 0373 Oslo")
        self.assertIn("<br/>", page.intro)  # single newline -> <br/>
        self.assertIn("</p><p>", page.intro)  # blank line -> paragraph break

        related = page.related_unions[0].value
        self.assertEqual(related["union"].pk, self.union.pk)
        self.assertEqual(related["role"], "host")

    @patch("ifi_home_app.management.commands.sync_peoply_events.get_events")
    def test_bedriftspresentasjon_title_is_tagged_company(self, mock_get_events):
        company_event = {
            **SAMPLE_EVENT,
            "id": "other-id",
            "title": "Bedriftspresentasjon med DNB",
        }
        mock_get_events.return_value = [company_event]

        call_command("sync_peoply_events")

        page = EventPage.objects.get(external_uid="other-id")
        self.assertEqual(page.event_type, "company")

    @patch("ifi_home_app.management.commands.sync_peoply_events.get_events")
    def test_converts_utc_start_to_local_date_and_time(self, mock_get_events):
        mock_get_events.return_value = [SAMPLE_EVENT]

        call_command("sync_peoply_events")

        page = EventPage.objects.get(external_uid=SAMPLE_EVENT["id"])
        self.assertEqual(page.event_date.isoformat(), "2026-01-16")
        self.assertEqual(page.event_time.strftime("%H:%M"), "20:00")

    @patch("ifi_home_app.management.commands.sync_peoply_events.get_events")
    def test_rerun_does_not_duplicate(self, mock_get_events):
        mock_get_events.return_value = [SAMPLE_EVENT]

        call_command("sync_peoply_events")
        call_command("sync_peoply_events")

        self.assertEqual(
            EventPage.objects.filter(
                external_source="peoply", external_uid=SAMPLE_EVENT["id"]
            ).count(),
            1,
        )

    @patch("ifi_home_app.management.commands.sync_peoply_events.get_events")
    def test_union_without_peoply_id_is_skipped(self, mock_get_events):
        mock_get_events.return_value = []
        _make_union(title="No Peoply", slug="no-peoply", peoply_organization_id="")

        call_command("sync_peoply_events")

        # Only the one union with an id set should have triggered a call.
        mock_get_events.assert_called_once()
        self.assertEqual(mock_get_events.call_args[0][0], "test-org-id")


FUTURE_EVENT = {
    **SAMPLE_EVENT,
    "id": "future-id",
    "urlId": "FUTURE",
    "title": "Julebord",
    "startDate": "2099-12-01T17:00:00.000Z",  # 18:00 Oslo
    "endDate": "2099-12-01T21:00:00.000Z",
}


class SyncPeoplyUpdatesAndRemovalsTests(TestCase):
    """sync_peoply_events treating Peoply as the source of truth: updating
    already-synced events, and hiding/logging ones gone from Peoply."""

    def setUp(self):
        self.union = _make_union(peoply_organization_id="test-org-id")
        self.event_index = _make_event_index()
        patcher = patch(
            "ifi_home_app.management.commands.check_peoply_union_matches.get_organizations",
            return_value=[],
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        events_patcher = patch(
            "ifi_home_app.management.commands.sync_peoply_events.get_events"
        )
        self.mock_get_events = events_patcher.start()
        self.addCleanup(events_patcher.stop)

    def _sync(self, events):
        self.mock_get_events.return_value = events
        call_command("sync_peoply_events", stdout=StringIO())

    def _page(self, uid=FUTURE_EVENT["id"]):
        return EventPage.objects.get(external_uid=uid)

    def test_changes_on_peoply_update_existing_page(self):
        self._sync([FUTURE_EVENT])
        page = self._page()
        original_slug = page.slug
        page.event_type = "academic"  # editor-owned, must survive the resync
        page.save_revision().publish()

        self._sync(
            [
                {
                    **FUTURE_EVENT,
                    "title": "Julebord (flyttet)",
                    "startDate": "2099-12-02T18:00:00.000Z",
                    "endDate": "2099-12-02T22:00:00.000Z",
                    "freeformAddress": "Ny adresse 1",
                    "description": "Oppdatert.",
                }
            ]
        )

        page = self._page()
        self.assertEqual(page.title, "Julebord (flyttet)")
        self.assertEqual(page.event_date.isoformat(), "2099-12-02")
        self.assertEqual(page.event_time.strftime("%H:%M"), "19:00")
        self.assertEqual(page.event_end_time.strftime("%H:%M"), "23:00")
        self.assertEqual(page.location, "Ny adresse 1")
        self.assertEqual(page.intro, "<p>Oppdatert.</p>")
        self.assertEqual(page.slug, original_slug)
        self.assertEqual(page.event_type, "academic")

    def test_unchanged_event_gets_no_new_revision(self):
        self._sync([FUTURE_EVENT])
        revisions = self._page().revisions.count()

        self._sync([FUTURE_EVENT])

        self.assertEqual(self._page().revisions.count(), revisions)

    def test_switch_to_multi_day_clears_end_time(self):
        self._sync([FUTURE_EVENT])
        self.assertIsNotNone(self._page().event_end_time)

        self._sync([{**FUTURE_EVENT, "endDate": "2099-12-04T21:00:00.000Z"}])

        page = self._page()
        self.assertIsNone(page.event_end_time)
        self.assertEqual(page.end_date.isoformat(), "2099-12-04")

    def test_event_gone_from_peoply_is_hidden_and_logged(self):
        self._sync([FUTURE_EVENT])

        self._sync([])

        page = self._page()
        self.assertFalse(page.live)
        removal = PeoplyRemovedEvent.objects.get(external_uid=FUTURE_EVENT["id"])
        self.assertIsNone(removal.resolved_at)
        self.assertEqual(removal.page_id, page.pk)

    def test_past_event_missing_from_fetch_is_not_hidden(self):
        # Peoply's afterDate filter never returns past events -- absence
        # there isn't removal.
        self._sync([SAMPLE_EVENT])

        self._sync([])

        self.assertTrue(self._page(SAMPLE_EVENT["id"]).live)
        self.assertFalse(PeoplyRemovedEvent.objects.exists())

    def test_events_of_unlinked_union_are_not_hidden(self):
        self._sync([FUTURE_EVENT])
        UnionPage.objects.filter(pk=self.union.pk).update(peoply_organization_id="")

        self._sync([])

        self.assertTrue(self._page().live)

    def test_editor_unpublished_event_is_not_republished(self):
        self._sync([FUTURE_EVENT])
        self._page().unpublish()

        self._sync([{**FUTURE_EVENT, "title": "Changed"}])

        self.assertFalse(self._page().live)

    def test_reappearing_event_is_restored_and_log_resolved(self):
        self._sync([FUTURE_EVENT])
        self._sync([])

        self._sync([FUTURE_EVENT])

        self.assertTrue(self._page().live)
        removal = PeoplyRemovedEvent.objects.get(external_uid=FUTURE_EVENT["id"])
        self.assertIsNotNone(removal.resolved_at)
        self.assertEqual(removal.resolution, "reappeared")


class PeoplyRemovedEventAdminTests(TestCase):
    """PeoplyRemovedEventAdmin's archive/delete actions."""

    def setUp(self):
        self.union = _make_union(peoply_organization_id="test-org-id")
        self.event_index = _make_event_index()
        with patch(
            "ifi_home_app.management.commands.check_peoply_union_matches.get_organizations",
            return_value=[],
        ), patch(
            "ifi_home_app.management.commands.sync_peoply_events.get_events"
        ) as mock_get_events:
            mock_get_events.return_value = [FUTURE_EVENT]
            call_command("sync_peoply_events", stdout=StringIO())
            mock_get_events.return_value = []
            call_command("sync_peoply_events", stdout=StringIO())
        self.removal = PeoplyRemovedEvent.objects.get(external_uid=FUTURE_EVENT["id"])

        superuser = get_user_model().objects.create_superuser(
            "admin", "admin@test.com", "pw"
        )
        self.client.force_login(superuser)

    def _post_action(self, action):
        return self.client.post(
            reverse("admin:ifi_home_app_peoplyremovedevent_changelist"),
            {"action": action, "_selected_action": [str(self.removal.pk)]},
            follow=True,
        )

    def test_archive_republishes_under_previous_events_only(self):
        self._post_action("archive_events")

        page = EventPage.objects.get(external_uid=FUTURE_EVENT["id"])
        self.assertTrue(page.live)
        self.assertTrue(page.is_archived)
        self.removal.refresh_from_db()
        self.assertEqual(self.removal.resolution, "archived")

        context = self.event_index.get_context(RequestFactory().get("/"))
        past = [e for group in context["past_month_groups"] for e in group["events"]]
        upcoming = [e for group in context["month_groups"] for e in group["events"]]
        self.assertIn(page, past)
        self.assertNotIn(page, upcoming)
        self.assertEqual(upcoming_events_for_union(self.union), [])

    def test_delete_removes_event_page(self):
        self._post_action("delete_event_pages")

        self.assertFalse(
            EventPage.objects.filter(external_uid=FUTURE_EVENT["id"]).exists()
        )
        self.removal.refresh_from_db()
        self.assertEqual(self.removal.resolution, "deleted")
        self.assertIsNone(self.removal.page)


class EventPageFormTests(TestCase):
    """EventPageForm locks PEOPLY_SYNCED_FIELDS on peoply-sourced events."""

    def _form(self, page):
        form_class = EventPage.get_edit_handler().get_form_class()
        return form_class(instance=page, for_user=get_user_model()(is_superuser=True))

    def test_synced_fields_disabled_for_peoply_event(self):
        form = self._form(EventPage(external_source="peoply"))
        for name in ("title", "event_date", "location", "intro"):
            self.assertTrue(form.fields[name].disabled, name)
        self.assertFalse(form.fields["event_type"].disabled)

    def test_manual_event_fields_editable(self):
        form = self._form(EventPage())
        self.assertFalse(form.fields["title"].disabled)


class CheckPeoplyUnionMatchesTests(TestCase):
    """The check_peoply_union_matches management command."""

    def _patch_organizations(self, orgs):
        patcher = patch(
            "ifi_home_app.management.commands.check_peoply_union_matches.get_organizations",
            return_value=orgs,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_matched_id_produces_no_warnings(self):
        _make_union(peoply_organization_id="org-1")
        self._patch_organizations([_fake_org(id="org-1")])

        out = StringIO()
        call_command("check_peoply_union_matches", stdout=out)

        self.assertIn("Every union and Peoply organization matches up", out.getvalue())

    def test_union_with_no_id_but_exact_match_is_reported_pending_link_not_missing_org(
        self,
    ):
        union = _make_union(title="CYB", slug="cyb")
        self._patch_organizations([_fake_org(id="org-1", name="CYB", urlId="cyb")])

        out = StringIO()
        call_command("check_peoply_union_matches", stdout=out)

        self.assertIn(union.title, out.getvalue())
        self.assertIn("aren't linked yet", out.getvalue())
        self.assertNotIn("no matching union on this site", out.getvalue())
        self.assertTrue(
            PeoplyUnionMismatch.objects.filter(
                kind="pending_link", identifier=str(union.translation_key)
            ).exists()
        )

    def test_union_with_no_id_and_no_name_match_is_reported_unlinked(self):
        _make_union(title="Mystery Union", slug="mystery-union")
        self._patch_organizations(
            [_fake_org(id="org-1", name="Unrelated Org", urlId="unrelated")]
        )

        out = StringIO()
        call_command("check_peoply_union_matches", stdout=out)

        self.assertIn("Mystery Union", out.getvalue())
        self.assertIn("no matching Peoply organization", out.getvalue())

    def test_retired_union_with_no_match_is_not_reported(self):
        _make_union(title="Mystery Union", slug="mystery-union", status="retired")
        self._patch_organizations([])

        out = StringIO()
        call_command("check_peoply_union_matches", stdout=out)

        self.assertIn("Every union and Peoply organization matches up", out.getvalue())

    def test_stale_peoply_id_is_reported(self):
        union = _make_union(peoply_organization_id="gone-id")
        self._patch_organizations([_fake_org(id="org-1")])

        out = StringIO()
        call_command("check_peoply_union_matches", stdout=out)

        self.assertIn(union.title, out.getvalue())
        self.assertIn("no longer recognizes", out.getvalue())

    def test_org_with_no_union_is_reported_and_not_created_by_default(self):
        self._patch_organizations([_fake_org(id="org-1", name="New Org")])

        out = StringIO()
        call_command("check_peoply_union_matches", stdout=out)

        self.assertIn("New Org", out.getvalue())
        self.assertIn("no matching union on this site", out.getvalue())
        self.assertFalse(UnionPage.objects.filter(title="New Org").exists())

    def test_create_missing_creates_draft_stub_under_sole_category(self):
        category = _make_union_category()
        self._patch_organizations(
            [_fake_org(id="org-1", name="New Org", websiteUrl="https://neworg.example")]
        )

        out = StringIO()
        call_command("check_peoply_union_matches", "--create-missing", stdout=out)

        stub = UnionPage.objects.get(title="New Org")
        self.assertEqual(stub.get_parent().specific, category)
        self.assertEqual(stub.peoply_organization_id, "org-1")
        self.assertEqual(stub.website_url, "https://neworg.example")
        self.assertFalse(stub.live)  # draft only, not published

    def test_create_missing_without_a_category_raises(self):
        self._patch_organizations([_fake_org(id="org-1", name="New Org")])

        with self.assertRaises(CommandError):
            call_command("check_peoply_union_matches", "--create-missing")

    def test_first_sighting_is_persisted_and_reported_new(self):
        self._patch_organizations([_fake_org(id="org-1", name="New Org")])

        out = StringIO()
        call_command("check_peoply_union_matches", stdout=out)

        self.assertIn("NEW:", out.getvalue())
        record = PeoplyUnionMismatch.objects.get(kind="missing_org", identifier="org-1")
        self.assertIsNone(record.resolved_at)
        self.assertEqual(record.label, "New Org (testorg)")

    def test_repeat_sighting_is_reported_already_known_not_new(self):
        self._patch_organizations([_fake_org(id="org-1", name="New Org")])
        call_command("check_peoply_union_matches", stdout=StringIO())  # first sighting

        out = StringIO()
        call_command("check_peoply_union_matches", stdout=out)

        self.assertNotIn("NEW:", out.getvalue())
        self.assertIn("(already known)", out.getvalue())
        self.assertEqual(
            PeoplyUnionMismatch.objects.filter(
                kind="missing_org", identifier="org-1"
            ).count(),
            1,
        )

    def test_mismatch_no_longer_present_is_marked_resolved(self):
        self._patch_organizations([_fake_org(id="org-1", name="New Org")])
        call_command("check_peoply_union_matches", stdout=StringIO())  # first sighting

        self._patch_organizations(
            []
        )  # org-1 gone (e.g. someone linked/created the union)
        out = StringIO()
        call_command("check_peoply_union_matches", stdout=out)

        self.assertIn("marked resolved", out.getvalue())
        record = PeoplyUnionMismatch.objects.get(kind="missing_org", identifier="org-1")
        self.assertIsNotNone(record.resolved_at)

    def test_resolved_mismatch_reappearing_reopens_same_row_as_new(self):
        self._patch_organizations([_fake_org(id="org-1", name="New Org")])
        call_command("check_peoply_union_matches", stdout=StringIO())  # first sighting

        self._patch_organizations([])
        call_command("check_peoply_union_matches", stdout=StringIO())  # resolved

        self._patch_organizations([_fake_org(id="org-1", name="New Org")])
        out = StringIO()
        call_command("check_peoply_union_matches", stdout=out)  # reappears

        self.assertIn("NEW:", out.getvalue())
        self.assertEqual(
            PeoplyUnionMismatch.objects.filter(
                kind="missing_org", identifier="org-1"
            ).count(),
            1,
        )
        record = PeoplyUnionMismatch.objects.get(kind="missing_org", identifier="org-1")
        self.assertIsNone(record.resolved_at)
