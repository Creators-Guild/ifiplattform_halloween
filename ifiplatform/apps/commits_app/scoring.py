"""Turns Credit rows into points per person, for the leaderboard and Your
Page. Credits are per GitHub username; a GitHubLink ties one to a site
account. Ties go to whoever reached their points first."""

from dataclasses import dataclass, field

from django.conf import settings

from .models import Credit, GitHubLink


@dataclass
class Score:
    github_login: str
    points: int = 0
    issues: list = field(default_factory=list)
    reached_at: object = None  # when the latest credit landed
    user: object = None  # the linked site user, if any
    drink_given: bool = False

    @property
    def drink_earned(self):
        return self.points >= settings.DRINK_TICKET_POINTS


def scores_by_login():
    scores = {}
    for credit in Credit.objects.select_related("issue").order_by("credited_at"):
        score = scores.setdefault(credit.github_login, Score(credit.github_login))
        score.points += credit.issue.points
        score.issues.append(credit.issue)
        score.reached_at = credit.credited_at
    for link in GitHubLink.objects.select_related("user", "user__drink_ticket"):
        if link.github_login in scores:
            scores[link.github_login].user = link.user
            scores[link.github_login].drink_given = hasattr(link.user, "drink_ticket")
    return scores


def leaderboard():
    """(linked, unlinked): Scores with and without a site account, best first."""
    scores = sorted(scores_by_login().values(), key=lambda s: (-s.points, s.reached_at))
    return [s for s in scores if s.user], [s for s in scores if not s.user]


def score_for(github_login):
    return scores_by_login().get(github_login, Score(github_login))
