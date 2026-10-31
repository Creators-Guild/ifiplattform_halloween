"""Which rule gave each Credit, worked out afterwards for the admin list and
halloween_totals, so both agree. Same order as github_sync._credit, against
the overrides, claims and links as they are now."""

from django.db.models import Case, Exists, OuterRef, Value, When

from .models import Claim, CreditOverride, GitHubLink

OVERRIDE = "override"
CLAIM = "claim"
GITHUB = "github"
SOURCES = [(OVERRIDE, "Override"), (CLAIM, "Claim"), (GITHUB, "GitHub")]


def with_source(credits):
    """Adds `source` (one of SOURCES) and `linked` (the login is on a site
    account's GitHubLink) to a Credit queryset."""
    return credits.annotate(
        source=Case(
            When(
                Exists(
                    CreditOverride.objects.filter(
                        issue_number=OuterRef("issue__number")
                    )
                ),
                then=Value(OVERRIDE),
            ),
            When(
                Exists(
                    Claim.objects.filter(
                        issue_number=OuterRef("issue__number"),
                        user__github_link__github_login=OuterRef("github_login"),
                    )
                ),
                then=Value(CLAIM),
            ),
            default=Value(GITHUB),
        ),
        linked=Exists(GitHubLink.objects.filter(github_login=OuterRef("github_login"))),
    )
