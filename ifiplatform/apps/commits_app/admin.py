# pylint: disable=C0114,C0115,C0116
from django.contrib import admin, messages

from .credit_source import SOURCES, with_source
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


class SourceFilter(admin.SimpleListFilter):
    title = "how credited"
    parameter_name = "source"

    def lookups(self, request, model_admin):
        return SOURCES

    def queryset(self, request, queryset):
        return queryset.filter(source=self.value()) if self.value() else queryset


class LinkedFilter(admin.SimpleListFilter):
    title = "linked on site"
    parameter_name = "linked"

    def lookups(self, request, model_admin):
        return [("yes", "Yes"), ("no", "No")]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(linked=self.value() == "yes")
        return queryset


@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
    list_display = [
        "issue", "github_login", "pr_number", "credited_at", "source", "linked"
    ]
    list_filter = [SourceFilter, LinkedFilter]
    search_fields = ["github_login"]

    def get_queryset(self, request):
        return with_source(super().get_queryset(request))

    @admin.display(description="How credited", ordering="source")
    def source(self, obj):
        return dict(SOURCES)[obj.source]

    @admin.display(description="Linked on site", boolean=True, ordering="linked")
    def linked(self, obj):
        return obj.linked


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
