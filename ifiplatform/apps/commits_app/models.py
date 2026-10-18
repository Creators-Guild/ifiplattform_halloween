"""The event points system on the Halloween mock site: GitHub issues and who
solved them (both copied from GitHub by github_sync.py), the link between a
site account and a GitHub username, drink tickets, and the helpers'
solutions. Only public GitHub data is stored here -- usernames, issue and PR
numbers, titles and labels."""

from django.conf import settings
from django.db import models

from .labels import CATEGORY_SLUGS, contest_points_for, difficulty_text, size_label


class EventIssue(models.Model):
    """A GitHub issue that is part of the event: it has a size label, or it
    is the parent of one that has. Written by the sync only."""

    number = models.PositiveIntegerField(unique=True)
    title = models.CharField(max_length=300)
    url = models.URLField()
    state = models.CharField(max_length=10)  # "OPEN" / "CLOSED", as GitHub says
    category = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=20, blank=True)
    # The coins for the drink ticket (see labels.py). Named "points" because it
    # predates the contest points; 0 for a parent issue and for unsized ones.
    points = models.PositiveSmallIntegerField(default=0)
    parent_number = models.PositiveIntegerField(null=True, blank=True)
    assignees = models.JSONField(
        default=list, blank=True, help_text="GitHub usernames, lowercased."
    )
    needs_look = models.BooleanField(
        default=False,
        help_text="Set by the sync when a PR closes more than one event issue -- "
        "settle it with a CreditOverride.",
    )

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"#{self.number} {self.title}"

    @property
    def coins(self):
        return self.points

    @property
    def contest_points(self):
        """The leaderboard points this issue gives; 0 for a parent issue."""
        return contest_points_for(self.size) if self.points else 0

    @property
    def size_label(self):
        return size_label(self.size)

    @property
    def difficulty_text(self):
        return difficulty_text(self.size)

    @property
    def category_slug(self):
        return CATEGORY_SLUGS.get(self.category, "")


class Credit(models.Model):
    """Who gets the points for an issue. Rebuilt by every sync, so edits here
    don't last -- use CreditOverride to fix credit by hand."""

    issue = models.OneToOneField(
        EventIssue, on_delete=models.CASCADE, related_name="credit"
    )
    github_login = models.CharField(max_length=39)  # lowercased
    pr_number = models.PositiveIntegerField(null=True, blank=True)
    credited_at = models.DateTimeField()

    class Meta:
        ordering = ["credited_at"]

    def __str__(self):
        return f"#{self.issue.number} -> {self.github_login}"


class CreditOverride(models.Model):
    """An organiser's decision on who gets an issue's points. The sync uses
    it before its own rules, so it survives every later sync."""

    issue_number = models.PositiveIntegerField(unique=True)
    github_login = models.CharField(max_length=39)

    def save(self, *args, **kwargs):
        self.github_login = self.github_login.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"#{self.issue_number} -> {self.github_login}"


class SyncStatus(models.Model):
    """One row: how the last sync went. In the database rather than the
    cache, because every deploy runs clear_cache."""

    last_attempt_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    open_pr_logins = models.JSONField(
        default=list,
        blank=True,
        help_text="GitHub usernames (lowercased) with an open PR in the event repo "
        "at the last sync. Their claims get no time limit (claims.py).",
    )

    class Meta:
        verbose_name_plural = "sync status"

    @classmethod
    def get(cls):
        status, _ = cls.objects.get_or_create(pk=1)
        return status

    def __str__(self):
        return "Sync status"


class GitHubLink(models.Model):
    """The GitHub username a participant typed on the Commits page. Not proven to be
    theirs (there's no GitHub login) -- organisers fix wrong ones here."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="github_link"
    )
    github_login = models.CharField(max_length=39, unique=True)  # lowercased

    def save(self, *args, **kwargs):
        self.github_login = self.github_login.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} = {self.github_login}"


class DrinkTicket(models.Model):
    """Marks that an organiser has handed this user their drink ticket."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="drink_ticket"
    )
    handed_out_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Drink ticket: {self.user}"


class EventSolution(models.Model):
    """A helper's solution for one issue, loaded from a private file by
    load_event_solutions. Keyed by number rather than a foreign key, so it
    survives whatever the sync does to EventIssue."""

    issue_number = models.PositiveIntegerField(unique=True)
    note = models.TextField(blank=True)
    diff = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["issue_number"]

    def __str__(self):
        return f"Solution for #{self.issue_number}"


class Claim(models.Model):
    """A participant's claim on an open issue, made on the Commits pages
    instead of a GitHub assignment (rules in claims.py). Keyed by number, like
    EventSolution, so it survives the sync. The unique number is what makes
    two people clicking at once safe: only one insert wins. Kept after the
    issue closes, because the sync credits the claimer (github_sync.py)."""

    issue_number = models.PositiveIntegerField(unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="claims"
    )
    claimed_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True, blank=True, help_text="Empty means no time limit."
    )
    seen_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the claimer first opened the issue. Until then its card "
        "is highlighted on My issues.",
    )

    class Meta:
        ordering = ["claimed_at"]

    def __str__(self):
        return f"#{self.issue_number} claimed by {self.user}"
