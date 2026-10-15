# pylint: disable=C0114,C0115,C0116
from django.contrib import admin, messages

from .models import (
    Claim,
    Credit,
    CreditOverride,
    DrinkTicket,
    EventIssue,
    EventSolution,
    GitHubLink,
    SyncStatus,
)


@admin.register(EventIssue)
class EventIssueAdmin(admin.ModelAdmin):
    list_display = ["number", "title", "size", "points", "state", "needs_look"]
    list_filter = ["state", "size", "category", "needs_look"]
    search_fields = ["title", "number"]


@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
    list_display = ["issue", "github_login", "pr_number", "credited_at"]
    search_fields = ["github_login"]


@admin.register(CreditOverride)
class CreditOverrideAdmin(admin.ModelAdmin):
    list_display = ["issue_number", "github_login"]
    search_fields = ["github_login"]


@admin.register(GitHubLink)
class GitHubLinkAdmin(admin.ModelAdmin):
    list_display = ["user", "github_login"]
    search_fields = ["user__username", "github_login"]


@admin.register(DrinkTicket)
class DrinkTicketAdmin(admin.ModelAdmin):
    list_display = ["user", "handed_out_at"]


@admin.register(EventSolution)
class EventSolutionAdmin(admin.ModelAdmin):
    list_display = ["issue_number", "updated_at"]


@admin.register(SyncStatus)
class SyncStatusAdmin(admin.ModelAdmin):
    list_display = ["last_attempt_at", "last_success_at", "last_error"]


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ["issue_number", "user", "claimed_at", "expires_at"]
    search_fields = ["user__username", "issue_number"]
    actions = ["release"]

    @admin.action(description="Release selected claims (open issues only)")
    def release(self, request, queryset):
        """A closed issue's claim decides its points (github_sync.py), so
        those are skipped; change who gets them with a credit override."""
        open_numbers = EventIssue.objects.exclude(state="CLOSED").values("number")
        released, _ = queryset.filter(issue_number__in=open_numbers).delete()
        skipped = queryset.count()
        self.message_user(request, f"Released {released} claim(s).", messages.SUCCESS)
        if skipped:
            self.message_user(
                request,
                f"Kept {skipped} claim(s) on closed issues: they decide the points. "
                "Use a credit override instead.",
                messages.WARNING,
            )
