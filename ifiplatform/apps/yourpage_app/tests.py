# pylint: disable=C0114,C0115,C0116
import io
import json
from unittest import mock

from django.contrib.auth import get_user_model
from datetime import timedelta

from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone, translation

from yourpage_app import claims, github_sync
from yourpage_app.models import (
    Claim,
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

    def test_points_chip_on_every_commits_page(self):
        make_credit(1, "spooky")
        make_credit(2, "spooky", "🎃 pumpkin")
        pages = [
            reverse("yourpage_main"),
            reverse("yourpage_leaderboard"),
            reverse("yourpage_issues"),
            reverse("yourpage_issue_detail", args=[1]),
        ]
        for url in pages[1:]:
            self.assertNotContains(self.client.get(url), "my-points")
        self.client.login(username="ghostie", password="pw")
        self.assertContains(self.client.get(pages[2]), "Link your GitHub")
        self.link(self.user, "spooky")
        for url in pages:
            response = self.client.get(url)
            self.assertContains(response, "@spooky")
            # 4 points passes DRINK_TICKET_POINTS=3, so the chip shows the drink
            self.assertContains(response, "my-points--ready")
            self.assertContains(
                response, '<span class="my-points__pts">4 points 🍹</span>', html=True
            )

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

    def test_sync_now_for_helpers_and_organisers(self):
        sync_url = reverse("yourpage_sync_now")
        self.client.login(username="ghostie", password="pw")
        self.assertEqual(self.client.post(sync_url).status_code, 403)
        self.assertNotContains(self.client.get(reverse("yourpage_issues")), sync_url)
        for username in ["helper", "boss"]:
            self.client.login(username=username, password="pw")
            # the one button, in the tab bar on every Commits page
            for name in ["yourpage_issues", "yourpage_leaderboard", "yourpage_main"]:
                page = self.client.get(reverse(name))
                self.assertContains(page, f'action="{sync_url}"', count=1)
            response = self.client.post(
                sync_url, HTTP_REFERER="http://testserver/en/commits/issues/"
            )
            self.assertRedirects(
                response,
                "http://testserver/en/commits/issues/",
                fetch_redirect_response=False,
            )

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

    def test_several_categories_and_difficulties_can_be_picked(self):
        self.open_issue(1, "🍬 candy", "🦇 silly feature")
        self.open_issue(2, "🎃 pumpkin", "🎨 restyle")
        self.open_issue(3, "🍫 chocolate", "🧪 python")
        _response, groups = self.board(category=["🎨 restyle", "🦇 silly feature"])
        self.assertEqual(sorted(groups["open_groups"]), [1, 2])
        _response, groups = self.board(difficulty=["candy", "pumpkin"])
        self.assertEqual(sorted(groups["open_groups"]), [1, 2])

    def test_grouping_with_several_picked(self):
        self.open_issue(1, "🍬 candy", "🦇 silly feature")
        self.open_issue(2, "🎃 pumpkin", "🎨 restyle")
        self.open_issue(3, "🍬 candy", "🎨 restyle")
        # one category, two difficulties: grouped by difficulty, no choice
        response = self.client.get(
            reverse("yourpage_issues"),
            {"category": "🎨 restyle", "difficulty": ["candy", "pumpkin"]},
        )
        titles = [title for title, _groups in response.context["open_sections"]]
        self.assertEqual(titles, ["🍬 candy (easy)", "🎃 pumpkin (hard)"])
        self.assertEqual(response.context["group_pills"], [])
        # several of both: the visitor chooses again
        response = self.client.get(
            reverse("yourpage_issues"),
            {
                "category": ["🎨 restyle", "🦇 silly feature"],
                "difficulty": ["candy", "pumpkin"],
                "group": "difficulty",
            },
        )
        self.assertTrue(response.context["group_pills"])
        titles = [title for title, _groups in response.context["open_sections"]]
        self.assertEqual(titles, ["🍬 candy (easy)", "🎃 pumpkin (hard)"])

    def test_pills_toggle_their_value(self):
        response = self.client.get(reverse("yourpage_issues"), {"difficulty": "candy"})
        pills = {
            text: (url, active)
            for text, url, active, _c in response.context["difficulty_pills"]
        }
        candy_url, candy_active = pills["🍬 candy (easy)"]
        pumpkin_url, pumpkin_active = pills["🎃 pumpkin (hard)"]
        self.assertTrue(candy_active)
        self.assertFalse(pumpkin_active)
        self.assertNotIn("difficulty=candy", candy_url)
        self.assertIn("difficulty=candy", pumpkin_url)
        self.assertIn("difficulty=pumpkin", pumpkin_url)
        self.assertFalse(pills["All"][1])

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
        self.assertContains(response, "Your issues")
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

    def test_helpers_always_get_a_solution_button(self):
        make_credit(1, "someone")
        EventSolution.objects.create(issue_number=1, note="Edit footer.css", diff="")
        self.open_issue(2, "🍬 candy")
        board = reverse("yourpage_issues")
        missing = reverse("yourpage_issue_detail", args=[2])
        self.client.login(username="ghostie", password="pw")
        self.assertNotContains(self.client.get(board), "Solution")
        self.assertNotContains(self.client.get(missing), "Solution missing")
        self.client.login(username="helper", password="pw")
        response = self.client.get(board)
        self.assertContains(response, "🔑 Solution")
        self.assertContains(response, "Solution missing")
        self.assertContains(self.client.get(missing), "Solution missing")

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
        me = User.objects.create_user(username="me_user", password="pw")
        GitHubLink.objects.create(user=me, github_login="me")
        call_command(
            "seed_fake_points", "--me", "Me", "--extra", "5", stdout=io.StringIO()
        )
        self.assertEqual(EventIssue.objects.filter(number__gte=1000).count(), 5)
        self.assertTrue(EventIssue.objects.filter(number__gte=900).exists())
        self.assertEqual(Credit.objects.filter(github_login="me").count(), 2)
        # --me gets claims (Keep and Release work), not GitHub assignments
        self.assertEqual(Claim.objects.filter(user=me).count(), 2)
        self.assertFalse(
            any("me" in i.assignees for i in EventIssue.objects.filter(state="OPEN"))
        )
        self.assertEqual(Claim.objects.exclude(user=me).count(), 2)
        self.assertTrue(Credit.objects.exists())
        self.assertTrue(User.objects.filter(username__startswith="fake_").exists())
        self.assertEqual(
            set(EventSolution.objects.values_list("issue_number", flat=True)),
            set(EventIssue.objects.values_list("number", flat=True)),
        )
        call_command("seed_fake_points", "--clear", stdout=io.StringIO())
        self.assertFalse(EventSolution.objects.exists())
        self.assertFalse(Claim.objects.exists())
        self.assertFalse(EventIssue.objects.filter(number__gte=900).exists())
        self.assertFalse(User.objects.filter(username__startswith="fake_").exists())

    @override_settings(DEBUG=False)
    def test_refuses_without_debug(self):
        with self.assertRaises(Exception):
            call_command("seed_fake_points", stdout=io.StringIO())
        self.assertFalse(EventIssue.objects.exists())


SIZE_POINTS = {name: points for name, points in github_sync.SIZE_LABELS.values()}


@override_settings(
    GITHUB_READ_TOKEN="",
    CLAIM_LIMIT=2,
    CLAIM_MINUTES={"candy": 30, "chocolate": 60, "pumpkin": 90},
)
class ClaimTests(TestCase):
    """Claiming issues on the site (claims.py, the claim views, and the sync's
    credit for claimers)."""

    def setUp(self):
        self.enterContext(translation.override("en"))
        self.kari = self.linked("kari")
        self.ola = self.linked("ola")
        self.loner = User.objects.create_user(username="loner", password="pw")
        self.helper = User.objects.create_user(username="helpy", password="pw")
        group, _ = Group.objects.get_or_create(name="Helpers")
        self.helper.groups.add(group)

    def linked(self, name):
        user = User.objects.create_user(username=name, password="pw")
        GitHubLink.objects.create(user=user, github_login=name)
        return user

    def issue(self, number, size="candy", category="🎨 restyle", **fields):
        return EventIssue.objects.create(
            number=number,
            title=f"Issue {number}",
            url=f"https://github.com/o/r/issues/{number}",
            state=fields.pop("state", "OPEN"),
            size=size,
            points=SIZE_POINTS[size],
            category=category,
            **fields,
        )

    def post(self, user, name, *args, **data):
        self.client.force_login(user)
        response = self.client.post(
            reverse(name, args=args), data, HTTP_REFERER="http://testserver/x/"
        )
        return response, list(get_messages(response.wsgi_request))

    def test_claim_and_someone_faster_gets_an_alternative(self):
        self.issue(1)
        self.issue(2)
        response, _msgs = self.post(self.kari, "yourpage_claim", 1)
        self.assertRedirects(
            response, "http://testserver/x/", fetch_redirect_response=False
        )
        claim = Claim.objects.get(issue_number=1)
        self.assertEqual(claim.user, self.kari)
        self.assertAlmostEqual(
            (claim.expires_at - timezone.now()).total_seconds(), 30 * 60, delta=5
        )
        response = self.client.get(reverse("yourpage_issues"))
        self.assertContains(response, "#1 is yours!")
        self.assertContains(response, "See my issues")
        _response, msgs = self.post(self.ola, "yourpage_claim", 1)
        self.assertEqual(Claim.objects.get(issue_number=1).user, self.kari)
        self.assertIn("Just taken by kari", str(msgs[-1]))
        self.assertIn("claim-offer-2", msgs[-1].tags)

    def test_github_assigned_issue_is_taken(self):
        self.issue(1, assignees=["someone"])
        _response, msgs = self.post(self.kari, "yourpage_claim", 1)
        self.assertFalse(Claim.objects.exists())
        self.assertIn("claim-taken", msgs[-1].tags)

    def test_limit_and_unlinked(self):
        for number in (1, 2, 3):
            self.issue(number)
        self.post(self.kari, "yourpage_claim", 1)
        self.post(self.kari, "yourpage_claim", 2)
        _response, msgs = self.post(self.kari, "yourpage_claim", 3)
        self.assertFalse(Claim.objects.filter(issue_number=3).exists())
        self.assertIn("#1, #2", str(msgs[-1]))
        _response, msgs = self.post(self.loner, "yourpage_claim", 3)
        self.assertFalse(Claim.objects.filter(issue_number=3).exists())
        self.assertIn("Link your GitHub", str(msgs[-1]))

    def test_github_assignments_count_toward_the_limit(self):
        self.issue(1, assignees=["kari"])
        self.issue(2)
        self.issue(3)
        self.post(self.kari, "yourpage_claim", 2)
        _response, msgs = self.post(self.kari, "yourpage_claim", 3)
        self.assertFalse(Claim.objects.filter(issue_number=3).exists())
        self.assertIn("#1, #2", str(msgs[-1]))

    def test_github_assigned_card_explains_missing_buttons(self):
        self.issue(1, assignees=["kari"])
        self.client.force_login(self.kari)
        response = self.client.get(reverse("yourpage_main"))
        self.assertContains(response, "assigned to you on GitHub")
        self.assertNotContains(response, reverse("yourpage_release", args=[1]))

    def test_give_me_an_issue_is_greyed_out_at_the_limit(self):
        self.issue(1, assignees=["kari"])
        self.issue(2)
        self.issue(3)
        self.client.force_login(self.kari)
        response = self.client.get(reverse("yourpage_issues"))
        self.assertNotContains(response, 'aria-describedby="lucky-limit"')
        Claim.objects.create(issue_number=2, user=self.kari)
        response = self.client.get(reverse("yourpage_issues"))
        self.assertContains(response, 'disabled aria-describedby="lucky-limit"')
        self.assertContains(response, "You already have 2 issues (#1, #2)")

    def test_new_claim_is_highlighted_until_opened(self):
        self.issue(1)
        self.post(self.kari, "yourpage_claim", 1)
        main = reverse("yourpage_main")
        detail = reverse("yourpage_issue_detail", args=[1])
        self.assertContains(self.client.get(main), "issue-card--new")
        # someone else looking doesn't count
        self.client.force_login(self.ola)
        self.client.get(detail)
        self.client.force_login(self.kari)
        self.assertContains(self.client.get(main), "issue-card--new")
        self.client.get(detail)
        self.assertIsNotNone(Claim.objects.get(issue_number=1).seen_at)
        self.assertNotContains(self.client.get(main), "issue-card--new")

    def test_closed_claims_dont_count_toward_the_limit(self):
        self.issue(1, state="CLOSED")
        self.issue(2, state="CLOSED")
        self.issue(3)
        for number in (1, 2):
            Claim.objects.create(issue_number=number, user=self.kari)
        self.post(self.kari, "yourpage_claim", 3)
        self.assertTrue(Claim.objects.filter(issue_number=3).exists())

    def test_logged_out_cant_claim(self):
        self.issue(1)
        response = self.client.post(reverse("yourpage_claim", args=[1]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Claim.objects.exists())

    def test_time_depends_on_size_and_expired_claims_are_freed(self):
        now = timezone.now()
        self.issue(1, size="pumpkin")
        self.issue(2)
        self.issue(3)
        self.issue(4, state="CLOSED")
        self.post(self.kari, "yourpage_claim", 1)
        self.assertAlmostEqual(
            (Claim.objects.get(issue_number=1).expires_at - now).total_seconds(),
            90 * 60,
            delta=5,
        )
        past = now - timedelta(minutes=1)
        Claim.objects.create(issue_number=2, user=self.ola, expires_at=past)
        Claim.objects.create(issue_number=3, user=self.ola, expires_at=None)
        Claim.objects.create(issue_number=4, user=self.ola, expires_at=past)
        claims.release_expired()
        self.assertEqual(
            sorted(Claim.objects.values_list("issue_number", flat=True)), [1, 3, 4]
        )

    def test_keep_and_helper_time(self):
        self.issue(1, size="chocolate")
        Claim.objects.create(
            issue_number=1,
            user=self.kari,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        self.post(self.kari, "yourpage_keep", 1)
        left = claims.minutes_left(Claim.objects.get(issue_number=1))
        self.assertEqual(left, 60)
        response, _msgs = self.post(self.ola, "yourpage_claim_time", 1, action="plus15")
        self.assertEqual(response.status_code, 403)
        response, _msgs = self.post(self.ola, "yourpage_keep", 1)
        self.assertEqual(response.status_code, 403)
        self.post(self.helper, "yourpage_claim_time", 1, action="plus15")
        self.assertEqual(claims.minutes_left(Claim.objects.get(issue_number=1)), 75)
        self.post(self.helper, "yourpage_claim_time", 1, action="unlimited")
        self.assertIsNone(Claim.objects.get(issue_number=1).expires_at)
        self.post(self.helper, "yourpage_claim_time", 1, action="reset")
        self.assertEqual(claims.minutes_left(Claim.objects.get(issue_number=1)), 60)

    def test_release_rules(self):
        self.issue(1)
        self.issue(2, state="CLOSED")
        Claim.objects.create(issue_number=1, user=self.kari, expires_at=None)
        Claim.objects.create(issue_number=2, user=self.kari, expires_at=None)
        response, _msgs = self.post(self.ola, "yourpage_release", 1)
        self.assertEqual(response.status_code, 403)
        _response, msgs = self.post(self.helper, "yourpage_release", 1)
        self.assertFalse(Claim.objects.filter(issue_number=1).exists())
        self.assertIn("Released #1 from kari", str(msgs[-1]))
        _response, msgs = self.post(self.helper, "yourpage_release", 2)
        self.assertTrue(Claim.objects.filter(issue_number=2).exists())
        self.assertIn("is closed", str(msgs[-1]))
        Claim.objects.create(issue_number=1, user=self.kari)
        self.post(self.kari, "yourpage_release", 1)
        self.assertFalse(Claim.objects.filter(issue_number=1).exists())

    def test_give_me_an_issue_shows_one_without_claiming(self):
        self.issue(1)
        self.issue(2, size="pumpkin", category="🧪 python")
        self.client.force_login(self.kari)
        response = self.client.get(reverse("yourpage_lucky"), {"size": "pumpkin"})
        detail = reverse("yourpage_issue_detail", args=[2])
        self.assertRedirects(
            response,
            f"{detail}?lucky=1&size=pumpkin&category=",
            fetch_redirect_response=False,
        )
        self.assertFalse(Claim.objects.exists())
        page = self.client.get(response.url)
        self.assertContains(page, "Try another")
        self.assertContains(page, "skip=2")
        self.assertContains(page, reverse("yourpage_claim", args=[2]))

    def test_try_another_skips_the_one_just_shown(self):
        self.issue(1)
        self.issue(2)
        self.client.force_login(self.kari)
        for _ in range(5):
            response = self.client.get(reverse("yourpage_lucky"), {"skip": 1})
            self.assertIn(reverse("yourpage_issue_detail", args=[2]), response.url)
        # the only free one is shown again rather than nothing
        Claim.objects.create(issue_number=2, user=self.ola)
        response = self.client.get(reverse("yourpage_lucky"), {"skip": 1})
        self.assertIn(reverse("yourpage_issue_detail", args=[1]), response.url)

    def test_give_me_an_issue_when_nothing_is_free(self):
        self.issue(1, assignees=["someone"])
        self.client.force_login(self.kari)
        response = self.client.get(reverse("yourpage_lucky"), {"size": "pumpkin"})
        self.assertRedirects(
            response, reverse("yourpage_issues"), fetch_redirect_response=False
        )
        msgs = list(get_messages(response.wsgi_request))
        self.assertIn("No free issues match", str(msgs[-1]))

    def test_own_shuffled_order_with_free_first(self):
        for number in range(1, 13):
            self.issue(number, assignees=["someone"] if number == 1 else [])

        def order(user):
            self.client.force_login(user)
            response = self.client.get(reverse("yourpage_issues"))
            return [i.number for i, _subs in response.context["open_sections"][0][1]]

        kari_order = order(self.kari)
        self.assertEqual(kari_order, order(self.kari))
        self.assertNotEqual(kari_order, order(self.ola))
        self.assertEqual(kari_order[-1], 1)

    def test_buttons_on_the_cards(self):
        self.issue(1)
        self.issue(2)
        Claim.objects.create(issue_number=2, user=self.kari)
        self.client.force_login(self.ola)
        response = self.client.get(reverse("yourpage_issues"))
        self.assertContains(response, reverse("yourpage_claim", args=[1]))
        self.assertContains(response, "claimed by kari")
        self.assertNotContains(response, reverse("yourpage_claim", args=[2]))
        self.client.force_login(self.kari)
        response = self.client.get(reverse("yourpage_main"))
        self.assertContains(response, reverse("yourpage_release", args=[2]))
        self.client.force_login(self.helper)
        response = self.client.get(reverse("yourpage_issue_detail", args=[2]))
        self.assertContains(response, "Force release")
        self.assertContains(response, reverse("yourpage_claim_time", args=[2]))

    def test_sync_credits_the_claimer(self):
        Claim.objects.create(issue_number=5, user=self.kari)
        Claim.objects.create(issue_number=6, user=self.ola)
        Claim.objects.create(issue_number=8, user=self.loner)  # unlinked: old rules
        CreditOverride.objects.create(issue_number=6, github_login="boss")
        at = "2026-10-19T18:00:00Z"
        github_sync.apply(
            [
                raw_issue(5, prs=[(70, "someone", at)]),
                raw_issue(6),
                raw_issue(7, prs=[(71, "author", at)]),
                raw_issue(8, assignees=["assignee"]),
                raw_issue(9, prs=[(72, "greedy", at)]),
                raw_issue(10, prs=[(72, "greedy", at)]),
            ]
        )
        credits = dict(Credit.objects.values_list("issue__number", "github_login"))
        self.assertEqual(credits[5], "kari")
        self.assertEqual(Credit.objects.get(issue__number=5).pr_number, 70)
        self.assertEqual(credits[6], "boss")
        self.assertEqual(credits[7], "author")
        self.assertEqual(credits[8], "assignee")
        self.assertNotIn(9, credits)
        Claim.objects.create(issue_number=9, user=self.kari)
        github_sync.apply(
            [
                raw_issue(9, prs=[(72, "greedy", at)]),
                raw_issue(10, prs=[(72, "greedy", at)]),
            ]
        )
        credits = dict(Credit.objects.values_list("issue__number", "github_login"))
        self.assertEqual(credits, {9: "kari", 10: "greedy"})

    def test_open_pr_locks_the_claim_for_good(self):
        raw = raw_issue(7, state="OPEN")
        github_sync.apply([raw])
        Claim.objects.create(issue_number=7, user=self.kari, expires_at=timezone.now())
        github_sync.apply([raw], open_pr_logins=["kari"])
        self.assertEqual(SyncStatus.get().open_pr_logins, ["kari"])
        self.assertIsNone(Claim.objects.get(issue_number=7).expires_at)
        github_sync.apply([raw], open_pr_logins=[])
        self.assertIsNone(Claim.objects.get(issue_number=7).expires_at)

    def test_sync_reads_open_prs(self):
        body = {
            "data": {
                "repository": {
                    "issues": {
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                        "nodes": [],
                    },
                    "pullRequests": {
                        "nodes": [{"author": {"login": "Kari"}}, {"author": None}]
                    },
                }
            }
        }
        with override_settings(GITHUB_READ_TOKEN="t"), mock.patch(
            "urllib.request.urlopen",
            return_value=io.BytesIO(json.dumps(body).encode()),
        ):
            self.assertTrue(github_sync.sync())
        self.assertEqual(SyncStatus.get().open_pr_logins, ["kari"])

    def test_admin_release_skips_closed(self):
        self.issue(1)
        self.issue(2, state="CLOSED")
        Claim.objects.create(issue_number=1, user=self.kari)
        Claim.objects.create(issue_number=2, user=self.kari)
        boss = User.objects.create_superuser("boss2", "b@example.com", "pw")
        self.client.force_login(boss)
        self.client.post(
            reverse("admin:yourpage_app_claim_changelist"),
            {
                "action": "release",
                "_selected_action": list(Claim.objects.values_list("pk", flat=True)),
            },
        )
        self.assertEqual(
            list(Claim.objects.values_list("issue_number", flat=True)), [2]
        )
