# pylint: disable=C0114,C0115,C0116
import io
import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from yourpage_app import github_sync
from yourpage_app.models import (
    Credit,
    CreditOverride,
    DrinkTicket,
    EventIssue,
    EventSolution,
    GitHubLink,
    SyncStatus,
)

User = get_user_model()


def raw_issue(
    number,
    labels=("🍬 candy",),
    state="CLOSED",
    reason="COMPLETED",
    prs=(),
    assignees=(),
    parent=None,
    closed_at="2026-10-19T18:30:00Z",
):
    """One issue as GitHub's GraphQL answers it. `prs` is (number, author,
    merged_at) tuples, all merged."""
    return {
        "number": number,
        "title": f"Issue {number}",
        "url": f"https://github.com/o/r/issues/{number}",
        "state": state,
        "stateReason": reason if state == "CLOSED" else None,
        "closedAt": closed_at if state == "CLOSED" else None,
        "labels": {"nodes": [{"name": name} for name in labels]},
        "parent": {"number": parent} if parent else None,
        "assignees": {"nodes": [{"login": login} for login in assignees]},
        "closedByPullRequestsReferences": {
            "nodes": [
                {"number": n, "merged": True, "mergedAt": at, "author": {"login": who}}
                for n, who, at in prs
            ]
        },
    }


def graphql_response(issues):
    body = {
        "data": {
            "repository": {
                "issues": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": issues,
                }
            }
        }
    }
    return io.BytesIO(json.dumps(body).encode())


@override_settings(GITHUB_READ_TOKEN="test-token")
class SyncTests(TestCase):
    def sync_with(self, issues):
        with mock.patch(
            "urllib.request.urlopen", return_value=graphql_response(issues)
        ):
            return github_sync.sync()

    def test_points_come_from_size_labels(self):
        self.sync_with(
            [
                raw_issue(1, labels=["🍬 candy"]),
                raw_issue(2, labels=["🍫 chocolate", "🎨 restyle"]),
                raw_issue(3, labels=["🎃 pumpkin"]),
                raw_issue(4, labels=["bug"]),
            ]
        )
        points = dict(EventIssue.objects.values_list("number", "points"))
        self.assertEqual(points, {1: 1, 2: 2, 3: 3})
        self.assertEqual(EventIssue.objects.get(number=2).category, "🎨 restyle")

    def test_first_merged_pr_author_is_credited(self):
        self.sync_with(
            [
                raw_issue(
                    1,
                    prs=[
                        (11, "Late", "2026-10-19T19:00:00Z"),
                        (10, "Early", "2026-10-19T18:10:00Z"),
                    ],
                )
            ]
        )
        credit = Credit.objects.get()
        self.assertEqual((credit.github_login, credit.pr_number), ("early", 10))

    def test_assignees_are_stored(self):
        self.sync_with([raw_issue(1, state="OPEN", assignees=["Ghost", "Bat"])])
        self.assertEqual(EventIssue.objects.get().assignees, ["ghost", "bat"])

    def test_assignee_is_credited_without_a_pr(self):
        self.sync_with([raw_issue(1, assignees=["Writer", "Other"])])
        credit = Credit.objects.get()
        self.assertEqual((credit.github_login, credit.pr_number), ("writer", None))

    def test_not_planned_gives_no_credit(self):
        self.sync_with([raw_issue(1, reason="NOT_PLANNED", assignees=["writer"])])
        self.assertFalse(Credit.objects.exists())

    def test_parent_gets_no_points(self):
        self.sync_with(
            [
                raw_issue(1, labels=[], assignees=["boss"]),
                raw_issue(2, parent=1, assignees=["kid"]),
            ]
        )
        parent = EventIssue.objects.get(number=1)
        self.assertEqual(parent.points, 0)
        self.assertFalse(hasattr(parent, "credit"))
        self.assertEqual(EventIssue.objects.get(number=2).parent_number, 1)

    def test_reopened_issue_loses_its_credit(self):
        self.sync_with([raw_issue(1, assignees=["writer"])])
        self.assertTrue(Credit.objects.exists())
        self.sync_with([raw_issue(1, state="OPEN", assignees=["writer"])])
        self.assertFalse(Credit.objects.exists())

    def test_github_failure_keeps_old_data(self):
        self.sync_with([raw_issue(1, assignees=["writer"])])
        with mock.patch(
            "urllib.request.urlopen",
            side_effect=github_sync.urllib.error.URLError("down"),
        ):
            self.assertFalse(github_sync.sync())
        self.assertEqual(Credit.objects.count(), 1)
        self.assertIn("down", SyncStatus.get().last_error)

    def test_graphql_errors_keep_old_data(self):
        self.sync_with([raw_issue(1, assignees=["writer"])])
        body = io.BytesIO(json.dumps({"errors": [{"message": "bad"}]}).encode())
        with mock.patch("urllib.request.urlopen", return_value=body):
            self.assertFalse(github_sync.sync())
        self.assertEqual(Credit.objects.count(), 1)

    def test_status_records_success(self):
        self.sync_with([])
        status = SyncStatus.get()
        self.assertIsNotNone(status.last_success_at)
        self.assertEqual(status.last_error, "")

    def test_override_wins_and_survives_a_resync(self):
        CreditOverride.objects.create(issue_number=1, github_login="Fixed")
        issue = raw_issue(1, prs=[(10, "author", "2026-10-19T18:10:00Z")])
        self.sync_with([issue])
        self.sync_with([issue])
        self.assertEqual(Credit.objects.get().github_login, "fixed")

    def test_pr_closing_two_issues_credits_neither(self):
        greedy = (10, "greedy", "2026-10-19T18:10:00Z")
        self.sync_with([raw_issue(1, prs=[greedy]), raw_issue(2, prs=[greedy])])
        self.assertFalse(Credit.objects.exists())
        self.assertEqual(EventIssue.objects.filter(needs_look=True).count(), 2)

    def test_removed_issue_is_deleted(self):
        self.sync_with([raw_issue(1), raw_issue(2)])
        self.sync_with([raw_issue(1)])
        self.assertEqual(list(EventIssue.objects.values_list("number", flat=True)), [1])

    @override_settings(GITHUB_READ_TOKEN="")
    def test_no_sync_without_token(self):
        with mock.patch("urllib.request.urlopen") as urlopen:
            self.assertFalse(github_sync.sync())
            github_sync.maybe_sync()
        urlopen.assert_not_called()

    def test_maybe_sync_runs_once_per_window(self):
        cache.delete(github_sync.SYNC_LOCK_KEY)
        with mock.patch.object(github_sync, "sync") as sync:
            github_sync.maybe_sync()
            github_sync.maybe_sync()
        self.assertEqual(sync.call_count, 1)

    def test_command_fails_loudly(self):
        with mock.patch(
            "urllib.request.urlopen",
            side_effect=github_sync.urllib.error.URLError("down"),
        ):
            with self.assertRaises(Exception):
                call_command("sync_github_points", stdout=io.StringIO())


def make_credit(number, login, points_label="🍬 candy", at="2026-10-19T18:30:00Z"):
    size, points = github_sync.SIZE_LABELS[points_label]
    issue = EventIssue.objects.create(
        number=number,
        title=f"Issue {number}",
        url=f"https://github.com/o/r/issues/{number}",
        state="CLOSED",
        size=size,
        points=points,
    )
    return Credit.objects.create(
        issue=issue,
        github_login=login,
        credited_at=github_sync._parse_time(at),  # pylint: disable=protected-access
    )


@override_settings(GITHUB_READ_TOKEN="", DRINK_TICKET_POINTS=3)
class PagesTests(TestCase):
    def setUp(self):
        # English pages, so the assertions can look for the English texts.
        self.enterContext(translation.override("en"))
        self.user = User.objects.create_user(username="ghostie", password="pw")
        self.helper = User.objects.create_user(username="helper", password="pw")
        self.helper.groups.add(Group.objects.get(name="Helpers"))
        self.organiser = User.objects.create_user(
            username="boss", password="pw", is_staff=True
        )

    def link(self, user, login):
        GitHubLink.objects.create(user=user, github_login=login)

    def test_public_pages_work_logged_out(self):
        make_credit(1, "someone")
        for name in ["yourpage_leaderboard", "yourpage_issues"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        response = self.client.get(reverse("yourpage_issue_detail", args=[1]))
        self.assertEqual(response.status_code, 200)

    def test_your_page_needs_login(self):
        response = self.client.get(reverse("yourpage_main"))
        self.assertEqual(response.status_code, 302)

    def test_linking_a_username(self):
        self.client.login(username="ghostie", password="pw")
        self.client.post(reverse("yourpage_main"), {"github_login": "Spooky-Dev"})
        self.assertEqual(
            GitHubLink.objects.get(user=self.user).github_login, "spooky-dev"
        )

    def test_unlinking_with_an_empty_name(self):
        self.link(self.user, "spooky")
        self.client.login(username="ghostie", password="pw")
        self.client.post(reverse("yourpage_main"), {"github_login": ""})
        self.assertFalse(GitHubLink.objects.filter(user=self.user).exists())

    def test_duplicate_username_is_refused_any_case(self):
        self.link(self.helper, "spooky")
        self.client.login(username="ghostie", password="pw")
        response = self.client.post(
            reverse("yourpage_main"), {"github_login": "SPOOKY"}
        )
        self.assertContains(response, "already linked")
        self.assertFalse(GitHubLink.objects.filter(user=self.user).exists())

    def test_invalid_username_is_refused(self):
        self.client.login(username="ghostie", password="pw")
        response = self.client.post(
            reverse("yourpage_main"), {"github_login": "-bad name"}
        )
        self.assertContains(response, "valid GitHub username")

    def test_your_page_shows_points_and_drink_progress(self):
        self.link(self.user, "spooky")
        make_credit(1, "spooky", "🍫 chocolate")
        self.client.login(username="ghostie", password="pw")
        response = self.client.get(reverse("yourpage_main"))
        self.assertContains(response, "2/3")
        make_credit(2, "spooky")
        response = self.client.get(reverse("yourpage_main"))
        self.assertContains(response, "Show this to get your drink!")

    def test_hint_when_nothing_is_credited(self):
        self.link(self.user, "spooky")
        self.client.login(username="ghostie", password="pw")
        response = self.client.get(reverse("yourpage_main"))
        self.assertContains(response, "Nothing credited to spooky yet")

    def test_linked_users_on_leaderboard_and_unlinked_only_counted(self):
        self.link(self.user, "spooky")
        make_credit(1, "spooky")
        make_credit(2, "stranger")
        response = self.client.get(reverse("yourpage_leaderboard"))
        self.assertEqual([r.user for r in response.context["rows"]], [self.user])
        self.assertContains(response, "1 contributor hasn")
        self.assertNotContains(response, "stranger")

    def test_unlinked_names_shown_to_helpers(self):
        make_credit(1, "stranger")
        self.client.login(username="helper", password="pw")
        self.assertContains(
            self.client.get(reverse("yourpage_leaderboard")), "stranger"
        )

    def test_tie_goes_to_whoever_got_there_first(self):
        self.link(self.user, "late")
        self.link(self.helper, "early")
        make_credit(1, "late", at="2026-10-19T19:00:00Z")
        make_credit(2, "early", at="2026-10-19T18:00:00Z")
        response = self.client.get(reverse("yourpage_leaderboard"))
        self.assertEqual(
            [r.user for r in response.context["rows"]], [self.helper, self.user]
        )

    def test_drink_button_only_for_organisers(self):
        self.link(self.user, "spooky")
        make_credit(1, "spooky", "🎃 pumpkin")
        url = reverse("yourpage_hand_out_drink", args=[self.user.pk])

        self.client.login(username="ghostie", password="pw")
        self.assertNotContains(self.client.get(reverse("yourpage_leaderboard")), url)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertFalse(DrinkTicket.objects.exists())

        self.client.login(username="boss", password="pw")
        self.assertContains(self.client.get(reverse("yourpage_leaderboard")), url)
        self.client.post(url)
        self.assertTrue(DrinkTicket.objects.filter(user=self.user).exists())

    def test_sync_now_only_for_organisers(self):
        self.client.login(username="ghostie", password="pw")
        self.assertEqual(
            self.client.post(reverse("yourpage_sync_now")).status_code, 403
        )
        self.client.login(username="boss", password="pw")
        response = self.client.post(reverse("yourpage_sync_now"))
        self.assertRedirects(response, reverse("yourpage_leaderboard"))

    def test_organiser_sees_missing_token_warning(self):
        self.client.login(username="boss", password="pw")
        response = self.client.get(reverse("yourpage_leaderboard"))
        self.assertContains(response, "No GitHub token is set")

    def board(self, **params):
        response = self.client.get(reverse("yourpage_issues"), params)
        return response, {
            name.replace("sections", "groups"): [
                issue.number
                for _title, groups in response.context[name]
                for issue, _subs in groups
            ]
            for name in ["open_sections", "closed_sections"]
        }

    def open_issue(self, number, label, category=""):
        size, points = github_sync.SIZE_LABELS[label]
        return EventIssue.objects.create(
            number=number,
            title=f"Issue {number}",
            url="https://x",
            state="OPEN",
            size=size,
            points=points,
            category=category,
        )

    def test_issue_board_sorts_by_category_then_difficulty(self):
        self.open_issue(1, "🍬 candy", "🦇 silly feature")
        self.open_issue(2, "🎃 pumpkin", "🎨 restyle")
        self.open_issue(3, "🍬 candy", "🎨 restyle")
        response, groups = self.board()
        self.assertEqual(groups["open_groups"], [3, 2, 1])
        self.assertContains(response, "🍬 candy")

    def test_sections_get_a_title_per_group(self):
        self.open_issue(1, "🍬 candy", "🦇 silly feature")
        self.open_issue(2, "🎃 pumpkin", "🎨 restyle")
        self.open_issue(3, "🍬 candy", "🎨 restyle")
        response = self.client.get(reverse("yourpage_issues"))
        titles = [title for title, _groups in response.context["open_sections"]]
        self.assertEqual(titles, ["🎨 restyle", "🦇 silly feature"])
        response = self.client.get(reverse("yourpage_issues"), {"group": "difficulty"})
        titles = [title for title, _groups in response.context["open_sections"]]
        self.assertEqual(titles, ["🍬 candy (easy)", "🎃 pumpkin (hard)"])

    def section_titles(self, **params):
        response = self.client.get(reverse("yourpage_issues"), params)
        return [title for title, _groups in response.context["open_sections"]]

    def test_grouping_follows_the_filters(self):
        self.open_issue(1, "🍬 candy", "🦇 silly feature")
        self.open_issue(2, "🎃 pumpkin", "🎨 restyle")
        self.open_issue(3, "🍬 candy", "🎨 restyle")
        # one category picked: grouped by difficulty, even if asked otherwise
        self.assertEqual(
            self.section_titles(category="🎨 restyle", group="category"),
            ["🍬 candy (easy)", "🎃 pumpkin (hard)"],
        )
        # one difficulty picked: grouped by category
        self.assertEqual(
            self.section_titles(difficulty="candy"),
            ["🎨 restyle", "🦇 silly feature"],
        )
        # both picked: one untitled list
        self.assertEqual(
            self.section_titles(category="🎨 restyle", difficulty="candy"), [""]
        )

    def test_group_choice_only_when_both_filters_are_all(self):
        response = self.client.get(reverse("yourpage_issues"))
        self.assertTrue(response.context["group_pills"])
        response = self.client.get(reverse("yourpage_issues"), {"difficulty": "candy"})
        self.assertEqual(response.context["group_pills"], [])

    def test_filter_links_keep_the_other_filter(self):
        response = self.client.get(reverse("yourpage_issues"), {"difficulty": "candy"})
        urls = [pill[1] for pill in response.context["category_pills"]]
        self.assertTrue(all("difficulty=candy" in url for url in urls))

    def test_issue_board_can_sort_by_difficulty(self):
        self.open_issue(1, "🍬 candy", "🦇 silly feature")
        self.open_issue(2, "🎃 pumpkin", "🎨 restyle")
        self.open_issue(3, "🍫 chocolate", "🎨 restyle")
        _response, groups = self.board(group="difficulty")
        self.assertEqual(groups["open_groups"], [1, 3, 2])

    def test_assigned_issue_shows_who_instead_of_free(self):
        self.link(self.user, "spooky")
        issue = self.open_issue(1, "🍬 candy")
        issue.assignees = ["spooky"]
        issue.save()
        response = self.client.get(reverse("yourpage_issues"))
        self.assertContains(response, "assigned to ghostie")
        self.assertNotContains(response, ">free<")

    def test_unlinked_assignee_is_hidden_from_public(self):
        issue = self.open_issue(1, "🍬 candy")
        issue.assignees = ["stranger"]
        issue.save()
        response = self.client.get(reverse("yourpage_issues"))
        self.assertContains(response, "assigned")
        self.assertNotContains(response, "stranger")

    def test_commits_page_lists_your_assigned_and_closed(self):
        self.link(self.user, "spooky")
        mine = self.open_issue(1, "🍬 candy")
        mine.assignees = ["spooky"]
        mine.save()
        other = self.open_issue(2, "🍬 candy")
        other.assignees = ["someone"]
        other.save()
        make_credit(3, "spooky")
        self.client.login(username="ghostie", password="pw")
        response = self.client.get(reverse("yourpage_main"))
        assigned = [i.number for i, _subs in response.context["assigned_groups"]]
        closed = [i.number for i, _subs in response.context["closed_groups"]]
        self.assertEqual((assigned, closed), ([1], [3]))
        self.assertContains(response, "Your assigned issues")
        self.assertContains(response, "Your closed issues")

    def test_closed_issues_go_below(self):
        self.open_issue(1, "🍬 candy")
        make_credit(2, "someone")
        response, groups = self.board()
        self.assertEqual(groups, {"open_groups": [1], "closed_groups": [2]})
        self.assertContains(response, "Done and closed")

    def test_difficulty_filter(self):
        make_credit(1, "a", "🎃 pumpkin")
        make_credit(2, "b", "🍬 candy")
        response = self.client.get(
            reverse("yourpage_issues"), {"difficulty": "pumpkin"}
        )
        _response, groups = self.board(difficulty="pumpkin")
        self.assertEqual(groups["closed_groups"], [1])
        self.assertContains(response, "🎃 pumpkin (hard)")

    def test_issue_board_hides_unlinked_names_from_public(self):
        make_credit(1, "stranger")
        response = self.client.get(reverse("yourpage_issues"))
        self.assertContains(response, "done")
        self.assertNotContains(response, "stranger")

    def test_solutions_only_for_helpers_and_organisers(self):
        make_credit(1, "someone")
        EventSolution.objects.create(issue_number=1, note="Edit footer.css", diff="+ x")
        detail = reverse("yourpage_issue_detail", args=[1])

        self.assertNotContains(self.client.get(detail), "Edit footer.css")
        self.assertNotContains(self.client.get(reverse("yourpage_issues")), "Solution")
        self.client.login(username="ghostie", password="pw")
        self.assertNotContains(self.client.get(detail), "Edit footer.css")

        for username in ["helper", "boss"]:
            self.client.login(username=username, password="pw")
            self.assertContains(self.client.get(detail), "Edit footer.css")
            self.assertContains(self.client.get(reverse("yourpage_issues")), "Solution")

    def test_issue_page_shows_parent_and_pr(self):
        self.open_issue(1, "🍬 candy", "🎨 restyle")
        credit = make_credit(2, "someone")
        credit.pr_number = 57
        credit.save()
        EventIssue.objects.filter(number=2).update(parent_number=1)
        response = self.client.get(reverse("yourpage_issue_detail", args=[2]))
        self.assertContains(response, "https://github.com/o/r/pull/57")
        self.assertContains(response, "#1 Issue 1")
        self.assertContains(response, "data-issue-panel")
        self.assertNotContains(response, "someone")

    @override_settings(OPEN_SIGNUP=True)
    def test_deleting_the_account_deletes_link_and_ticket(self):
        self.link(self.user, "spooky")
        DrinkTicket.objects.create(user=self.user)
        self.client.login(username="ghostie", password="pw")
        self.client.post(
            reverse("delete_account"),
            {
                "password": "pw",
                "study_tools_action": "delete",
                "articles_attribution": "unknown",
            },
        )
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        self.assertFalse(GitHubLink.objects.exists())
        self.assertFalse(DrinkTicket.objects.exists())


class LoadSolutionsTests(TestCase):
    def load(self, entries):
        with mock.patch("sys.stdin", io.StringIO(json.dumps(entries))):
            call_command("load_event_solutions", stdout=io.StringIO())

    def test_loads_and_updates_instead_of_duplicating(self):
        self.load([{"issue": 3, "note": "first", "diff": "+a"}])
        self.load([{"issue": 3, "note": "second"}, {"issue": 4, "note": "other"}])
        self.assertEqual(EventSolution.objects.count(), 2)
        self.assertEqual(EventSolution.objects.get(issue_number=3).note, "second")

    def test_bad_entry_loads_nothing(self):
        with self.assertRaises(Exception):
            self.load([{"issue": 5}, {"note": "no number"}])
        self.assertFalse(EventSolution.objects.exists())


class SeedFakePointsTests(TestCase):
    @override_settings(DEBUG=True)
    def test_seeds_and_clears(self):
        call_command(
            "seed_fake_points", "--me", "Me", "--extra", "5", stdout=io.StringIO()
        )
        self.assertEqual(EventIssue.objects.filter(number__gte=1000).count(), 5)
        self.assertTrue(EventIssue.objects.filter(number__gte=900).exists())
        self.assertEqual(Credit.objects.filter(github_login="me").count(), 2)
        self.assertTrue(
            any("me" in i.assignees for i in EventIssue.objects.filter(state="OPEN"))
        )
        self.assertTrue(Credit.objects.exists())
        self.assertTrue(User.objects.filter(username__startswith="fake_").exists())
        call_command("seed_fake_points", "--clear", stdout=io.StringIO())
        self.assertFalse(EventIssue.objects.filter(number__gte=900).exists())
        self.assertFalse(User.objects.filter(username__startswith="fake_").exists())

    @override_settings(DEBUG=False)
    def test_refuses_without_debug(self):
        with self.assertRaises(Exception):
            call_command("seed_fake_points", stdout=io.StringIO())
        self.assertFalse(EventIssue.objects.exists())
