"""Admin registration for ifi_home_app models."""

from django.contrib import admin, messages
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.text import slugify

import requests
from wagtail.coreutils import find_available_slug
from wagtail.models import Locale

from .integrations.peoply_api import (
    apply_peoply_match,
    find_exact_match,
    get_organizations,
)
from .models import StudentUnion
from .models.article.unions import StudentUnionCategoryPage, UnionPage
from .models.event.peoply import (
    PeoplyOrgsWithoutUnion,
    PeoplyRemovedEvent,
    PeoplySyncLog,
    UnionsPendingPeoplyLink,
    UnionsWithoutPeoplyOrg,
    UnionsWithStalePeoplyLink,
)

admin.site.register(StudentUnion)


@admin.register(PeoplySyncLog)
class PeoplySyncLogAdmin(admin.ModelAdmin):
    """Read-only, superuser-only audit log of "Sync Peoply now" button
    clicks (event_views.force_sync_peoply_events) -- exists to attribute
    spammy/repeated manual syncs to whoever triggered them, not for
    day-to-day staff use, so even a plain staff user can't see it."""

    list_display = ["user", "triggered_at"]

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PeoplyRemovedEvent)
class PeoplyRemovedEventAdmin(admin.ModelAdmin):
    """Peoply-sourced events sync_peoply_events hid because Peoply stopped
    returning them (see PeoplyRemovedEvent's own docstring). Superuser-only,
    never editable -- the two actions below are the only ways to act on one:
    archive it (republished, listed only under previous events) or delete
    the event page for good. An open row whose event reappears on Peoply is
    resolved by the sync itself."""

    list_display = [
        "title",
        "event_date",
        "first_seen_at",
        "last_seen_at",
        "resolution",
        "resolved_at",
        "page_link",
    ]
    list_filter = ["resolution"]
    actions = ["archive_events", "delete_event_pages", "delete_selected_logs"]

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_actions(self, request):
        # Built-in "delete_selected" would read as deleting the event
        # itself -- see _PeoplyUnionMismatchAdmin.get_actions.
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    @admin.display(description="Event page")
    def page_link(self, obj):
        if obj.page_id is None:
            return "-"
        return format_html(
            '<a href="{}">Open in Wagtail</a>',
            reverse("wagtailadmin_pages:edit", args=[obj.page_id]),
        )

    def _open_targets(self, request, queryset):
        """Open rows whose page still exists, or None (after messaging) if
        the caller should stop."""
        if not request.user.is_superuser:
            self.message_user(
                request, "Only superusers can do this.", level=messages.ERROR
            )
            return None
        skipped = queryset.exclude(resolved_at__isnull=True, page__isnull=False)
        if skipped.exists():
            self.message_user(
                request,
                f"{skipped.count()} selected row(s) were already resolved or have no event page left, skipped.",
                level=messages.WARNING,
            )
        return list(queryset.filter(resolved_at__isnull=True, page__isnull=False))

    @admin.action(description="Archive: show under previous events")
    def archive_events(self, request, queryset):
        targets = self._open_targets(request, queryset)
        if not targets:
            return
        for removal in targets:
            page = removal.page.specific
            page.is_archived = True
            page.save_revision(user=request.user).publish(user=request.user)
            removal.resolved_at = timezone.now()
            removal.resolution = "archived"
            removal.save()
        self.message_user(
            request, f"Archived {len(targets)} event(s).", level=messages.SUCCESS
        )

    @admin.action(description="Delete the selected event page(s) permanently")
    def delete_event_pages(self, request, queryset):
        targets = self._open_targets(request, queryset)
        if not targets:
            return
        for removal in targets:
            removal.page.delete()
            removal.page = None  # already SET_NULL in the DB by the delete above
            removal.resolved_at = timezone.now()
            removal.resolution = "deleted"
            removal.save()
        self.message_user(
            request, f"Deleted {len(targets)} event(s).", level=messages.SUCCESS
        )

    @admin.action(description="Delete selected log entries")
    def delete_selected_logs(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(
                request, "Only superusers can do this.", level=messages.ERROR
            )
            return
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request, f"Deleted {count} log entr{'y' if count == 1 else 'ies'}."
        )


class _PeoplyUnionMismatchAdmin(admin.ModelAdmin):
    """Shared base for the four PeoplyUnionMismatch proxies below (see
    their own docstrings, models/event/peoply.py, on why they're three separate
    admin entries rather than one combined filterable list). Superuser-only,
    and never editable -- but deletable, so stale/no-longer-interesting rows
    (e.g. already resolved_at) can be cleaned out by hand. Safe to delete
    freely: check_peoply_union_matches recreates a row from scratch the next
    time it sees that same (kind, identifier) mismatch again, it just won't
    remember first_seen_at from before the delete. `kind` isn't in
    list_display -- each proxy's own manager already restricts it to a
    single kind, so the column would be constant."""

    list_display = ["label", "first_seen_at", "last_seen_at", "resolved_at"]
    list_filter = ["resolved_at"]
    actions = ["delete_selected_logs"]

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_actions(self, request):
        # Drop the built-in "delete_selected" action -- its label quotes
        # this model's verbose_name ("site union without a Peoply
        # organization"), which reads as deleting the actual UnionPage.
        # delete_selected_logs below is the same delete, worded to make
        # clear it's only the log row.
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    @admin.action(description="Delete selected log entries")
    def delete_selected_logs(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(
                request, "Only superusers can do this.", level=messages.ERROR
            )
            return
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request, f"Deleted {count} log entr{'y' if count == 1 else 'ies'}."
        )


@admin.register(UnionsWithoutPeoplyOrg)
class UnionsWithoutPeoplyOrgAdmin(_PeoplyUnionMismatchAdmin):
    """Site UnionPages with no peoply_organization_id and no exact Peoply
    name/urlId match -- never had a link. See check_peoply_union_matches's
    own docstring for the exact-match rule."""


@admin.register(UnionsWithStalePeoplyLink)
class UnionsWithStalePeoplyLinkAdmin(_PeoplyUnionMismatchAdmin):
    """Site UnionPages whose peoply_organization_id no longer matches any
    organization Peoply currently returns -- had a link, now broken.
    sync_peoply_events silently syncs nothing for these (Peoply's /events
    just returns no rows for an unknown organizationId), so this is the
    only thing that would ever surface it."""


@admin.register(PeoplyOrgsWithoutUnion)
class PeoplyOrgsWithoutUnionAdmin(_PeoplyUnionMismatchAdmin):
    """Peoply organizations with no matching UnionPage here at all. The
    only one of the three with an extra action attached -- creating a stub
    only makes sense in this direction, not the other two."""

    actions = ["delete_selected_logs", "create_union_pages_for_missing_orgs"]

    @admin.action(description="Create a draft UnionPage for the selected mismatch(es)")
    def create_union_pages_for_missing_orgs(self, request, queryset):
        # Belt-and-suspenders on top of has_module_permission/
        # has_view_permission already gating who can reach this changelist
        # at all -- actions with no explicit `permissions=` are otherwise
        # shown to anyone who can view the list.
        if not request.user.is_superuser:
            self.message_user(
                request, "Only superusers can do this.", level=messages.ERROR
            )
            return

        # queryset is already scoped to kind="missing_org" by this proxy's
        # own manager -- only resolved_at still needs excluding here.
        resolved_skipped = queryset.filter(resolved_at__isnull=False).count()
        targets = list(queryset.filter(resolved_at__isnull=True))

        if not targets:
            self.message_user(
                request,
                "Nothing to create -- selection had no open mismatch.",
                level=messages.WARNING,
            )
            return

        # Unlike the command's own CommandError (which exits the process),
        # an admin action has to degrade to a message + no-op instead of
        # ever bubbling a stack trace to a 500 page.
        try:
            nb_locale = Locale.objects.get(language_code="nb")
            categories = StudentUnionCategoryPage.objects.live().filter(
                locale=nb_locale
            )
            count = categories.count()
            if count != 1:
                self.message_user(
                    request,
                    f"Can't auto-create: expected exactly one live nb StudentUnionCategoryPage, "
                    f"found {count}. Use `python manage.py check_peoply_union_matches "
                    "--create-missing --parent-slug ...` instead.",
                    level=messages.ERROR,
                )
                return
            parent = categories.first()
            orgs_by_id = {org["id"]: org for org in get_organizations()}
        except (requests.RequestException, Locale.DoesNotExist) as exc:
            self.message_user(
                request,
                f"Couldn't fetch Peoply's organizations: {exc}",
                level=messages.ERROR,
            )
            return

        created = []
        gone_from_peoply = []
        for mismatch in targets:
            org = orgs_by_id.get(mismatch.identifier)
            if org is None:
                gone_from_peoply.append(mismatch.label)
                continue

            page = UnionPage(
                title=org["name"],
                slug=find_available_slug(parent, slugify(org["name"])),
                locale=nb_locale,
                peoply_organization_id=org["id"],
                website_url=org.get("websiteUrl") or "",
                status="unknown",
                live=False,  # draft only -- needs editor review before publish
            )
            parent.add_child(instance=page)
            page.save_revision()
            created.append(org["name"])

            mismatch.resolved_at = timezone.now()
            mismatch.save()

        if created:
            self.message_user(
                request,
                f"Created {len(created)} draft UnionPage stub(s): {', '.join(created)}. "
                "Review, fill in, and publish each by hand in wagtail-admin.",
                level=messages.SUCCESS,
            )
        if gone_from_peoply:
            self.message_user(
                request,
                f"{len(gone_from_peoply)} selected mismatch(es) no longer appear on Peoply, skipped: "
                + ", ".join(gone_from_peoply),
                level=messages.WARNING,
            )
        if resolved_skipped:
            self.message_user(
                request,
                f"{resolved_skipped} selected row(s) were already resolved, skipped.",
                level=messages.WARNING,
            )


@admin.register(UnionsPendingPeoplyLink)
class UnionsPendingPeoplyLinkAdmin(_PeoplyUnionMismatchAdmin):
    """Site UnionPages with no peoply_organization_id, but an exact title
    match against a Peoply organization -- check_peoply_union_matches only
    ever reports these (it's read-only); link_selected_unions below is the
    admin-side equivalent of running link_peoply_organizations --apply for
    just the selected row(s)."""

    actions = ["delete_selected_logs", "link_selected_unions"]

    @admin.action(
        description="Link selected union(s) to their matched Peoply organization"
    )
    def link_selected_unions(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(
                request, "Only superusers can do this.", level=messages.ERROR
            )
            return

        resolved_skipped = queryset.filter(resolved_at__isnull=False).count()
        targets = list(queryset.filter(resolved_at__isnull=True))

        if not targets:
            self.message_user(
                request,
                "Nothing to link -- selection had no open mismatch.",
                level=messages.WARNING,
            )
            return

        try:
            nb_locale = Locale.objects.get(language_code="nb")
            orgs = get_organizations()
        except (requests.RequestException, Locale.DoesNotExist) as exc:
            self.message_user(
                request,
                f"Couldn't fetch Peoply's organizations: {exc}",
                level=messages.ERROR,
            )
            return

        linked = []
        no_longer_matches = []
        gone = []
        for mismatch in targets:
            try:
                union = UnionPage.objects.get(
                    translation_key=mismatch.identifier, locale=nb_locale
                )
            except UnionPage.DoesNotExist:
                gone.append(mismatch.label)
                continue

            # Re-checked here, not trusted from the log row -- the union's
            # own peoply_organization_id or Peoply's own roster may have
            # changed since check_peoply_union_matches last ran.
            org = (
                None
                if union.peoply_organization_id
                else find_exact_match(union.title, orgs)
            )
            if org is None:
                no_longer_matches.append(mismatch.label)
                continue

            apply_peoply_match(union, org)
            linked.append(f"{union.title} -> {org['name']}")

            mismatch.resolved_at = timezone.now()
            mismatch.save()

        if linked:
            self.message_user(
                request,
                f"Linked {len(linked)} union(s): " + ", ".join(linked),
                level=messages.SUCCESS,
            )
        if no_longer_matches:
            self.message_user(
                request,
                f"{len(no_longer_matches)} selected row(s) no longer have an exact match (or already have an id), skipped: "
                + ", ".join(no_longer_matches),
                level=messages.WARNING,
            )
        if gone:
            self.message_user(
                request,
                f"{len(gone)} selected union(s) no longer exist, skipped: "
                + ", ".join(gone),
                level=messages.WARNING,
            )
        if resolved_skipped:
            self.message_user(
                request,
                f"{resolved_skipped} selected row(s) were already resolved, skipped.",
                level=messages.WARNING,
            )
