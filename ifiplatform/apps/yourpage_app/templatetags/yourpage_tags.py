"""Template tags for the Commits pages, e.g. the visitor's points in the tab bar."""

from django import template

from ..models import GitHubLink
from ..scoring import score_for

register = template.Library()


@register.inclusion_tag("core/my_points.html", takes_context=True)
def my_points(context):
    """The visitor's GitHub link and score, for the chip in the Commits tab
    bar (core/yourpage_nav.html). Counted like the leaderboard, so the two
    always agree."""
    user = context["request"].user
    if not user.is_authenticated:
        return {"show": False}
    link = GitHubLink.objects.filter(user=user).first()
    return {
        "show": True,
        "link": link,
        "score": score_for(link.github_login) if link else None,
    }
