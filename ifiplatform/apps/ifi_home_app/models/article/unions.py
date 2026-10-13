"""UnionPage and StudentUnionCategoryPage -- mutually coupled with each
other (a category whose only children are unions), but not with the
Article/Category cluster in pages.py beyond one-directional queries.

Design rationale/history: docs/claude_context/article_unions.md"""

from datetime import date, timedelta

from django.db import models
from django.utils import timezone
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Locale, Page

from .blocks import union_group_block
from ..event.calendar_layout import build_calendar_days, hour_range_for_events
from ..event.dates import group_events_by_month, semester_bounds, week_bounds
from ..page_mixins import BannerStyleMixin, EditorModeMixin, TranslationWarningMixin


# Model for a student union's own page, published under a StudentUnionCategoryPage
class UnionPage(TranslationWarningMixin, Page):  # pylint: disable=too-many-ancestors
    """A single student union's page: contact info, purpose, activities and members."""

    template = "info_articles/pages/union_page.html"

    email = models.EmailField(blank=True)
    logo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    purpose = RichTextField(blank=True, help_text="What the union is about.")
    activities = RichTextField(blank=True, help_text="Activities the union offers.")
    vedtekter = RichTextField(
        blank=True,
        help_text="Optional -- the union's bylaws/statutes, shown on its own page.",
    )
    vedtekter_url = models.URLField(
        blank=True,
        help_text="Optional -- link to the full bylaws/statutes elsewhere (e.g. a PDF or the union's own site), shown alongside the text above.",
    )

    TYPE_CHOICES = [
        ("general", "Open to everyone"),
        ("program", "Program-specific"),
    ]

    union_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="general",
        help_text="Whether this union is open to everyone or tied to a specific program.",
    )

    STATUS_CHOICES = [
        ("active", "Active"),
        ("retired", "Retired -- no longer active"),
        ("unknown", "Unknown -- can't confirm if still active"),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="active",
        help_text="Active unions are shown in the main listing, retired ones under 'Old, but not forgotten', and unknown ones (e.g. no working contact/website found) under 'Missing in action'.",
    )

    website_url = models.URLField(blank=True)
    union_links = StreamField(
        [
            (
                "link",
                blocks.StructBlock(
                    [
                        (
                            "label",
                            blocks.CharBlock(
                                help_text='e.g. "Bli medlem", "Meld interesse", "Søk verv".'
                            ),
                        ),
                        ("url", blocks.URLBlock()),
                    ]
                ),
            ),
        ],
        use_json_field=True,
        blank=True,
        help_text="Optional -- one or more sign-up/interest links, each with its own label (e.g. a membership form, a volunteer sign-up).",
    )
    peoply_organization_id = models.CharField(
        max_length=64,
        blank=True,
        help_text="Optional -- this union's organization ID on Peoply (from its Peoply page URL). Setting this enables automatic event sync via sync_peoply_events.",
    )
    CALENDAR_VISIBILITY_CHOICES = [
        ("auto", "Automatic -- hide when there are 4 or fewer events this semester"),
        ("always", "Always show"),
        ("never", "Never show"),
    ]
    calendar_visibility = models.CharField(
        max_length=10,
        choices=CALENDAR_VISIBILITY_CHOICES,
        default="auto",
        help_text="Whether to show this union's events calendar on its page.",
    )

    SOCIAL_PLATFORM_CHOICES = [
        ("facebook", "Facebook"),
        ("instagram", "Instagram"),
        ("discord", "Discord"),
        ("linkedin", "LinkedIn"),
        ("tiktok", "TikTok"),
        ("github", "GitHub"),
        ("slack", "Slack"),
        ("other", "Other"),
    ]

    social_links = StreamField(
        [
            (
                "social_link",
                blocks.StructBlock(
                    [
                        (
                            "platform",
                            blocks.ChoiceBlock(choices=SOCIAL_PLATFORM_CHOICES),
                        ),
                        ("url", blocks.URLBlock()),
                    ]
                ),
            ),
        ],
        use_json_field=True,
        blank=True,
    )

    member_count_intern = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of interns. Leave blank to hide.",
    )

    sitting_members = StreamField(
        [
            (
                "member",
                blocks.StructBlock(
                    [
                        (
                            "name",
                            blocks.CharBlock(
                                required=False,
                                help_text="Leave blank for a vacant position -- see UnionPage.open_positions.",
                            ),
                        ),
                        (
                            "role",
                            blocks.CharBlock(
                                help_text="Role within the union, e.g. Chair, Treasurer."
                            ),
                        ),
                        (
                            "role_nickname",
                            blocks.CharBlock(
                                required=False,
                                help_text='Optional informal name for the role, e.g. "Guild Master" for "Leader".',
                            ),
                        ),
                        (
                            "school_email",
                            blocks.EmailBlock(required=False),
                        ),
                        ("picture", ImageChooserBlock(required=False)),
                        (
                            "responsibilities",
                            blocks.ListBlock(
                                blocks.RichTextBlock(
                                    features=["bold", "italic"], required=False
                                ),
                                required=False,
                                help_text='One responsibility per item -- each renders as its own stacked box under a "Responsibilities" heading. Bold/italic supported, no links/lists.',
                            ),
                        ),
                        (
                            "availability",
                            blocks.ChoiceBlock(
                                choices=[
                                    ("filled", "Filled"),
                                    ("open", "Open now"),
                                    ("opening_soon", "Opening soon"),
                                ],
                                default="filled",
                                help_text='"Open now"/"Opening soon" also list this position under Open Positions, even if it has a sitting member too.',
                            ),
                        ),
                        (
                            "availability_note",
                            blocks.CharBlock(
                                required=False,
                                help_text='Optional -- shown next to the Open Positions badge, e.g. "After the next general assembly (generalforsamling)".',
                            ),
                        ),
                    ]
                ),
            ),
        ],
        use_json_field=True,
        blank=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("email"),
        FieldPanel("logo"),
        FieldPanel("union_type"),
        FieldPanel("status"),
        FieldPanel("purpose"),
        FieldPanel("activities"),
        FieldPanel("vedtekter"),
        FieldPanel("vedtekter_url"),
        FieldPanel("website_url"),
        FieldPanel("union_links"),
        FieldPanel("peoply_organization_id"),
        FieldPanel("calendar_visibility"),
        FieldPanel("social_links"),
        FieldPanel("member_count_intern"),
        FieldPanel("sitting_members"),
    ]

    parent_page_types = ["ifi_home_app.StudentUnionCategoryPage"]
    subpage_types = []  # union pages have no children

    @property
    def union_category(self):
        """The StudentUnionCategoryPage this union lives under."""
        return self.get_parent().specific

    @property
    def filled_positions(self):
        """sitting_members entries with a name to show."""
        return [block for block in self.sitting_members if block.value.get("name")]

    @property
    def open_positions(self):
        """sitting_members entries flagged open/opening_soon -- independent
        of filled_positions, so one entry can appear in both (see
        docs/claude_context/article_unions.md)."""
        return [
            block
            for block in self.sitting_members
            if block.value.get("availability", "filled") != "filled"
        ]

    @property
    def member_count_sitting(self):
        """Count of filled_positions -- no longer a manually-entered field,
        so it can't drift from the union's actual sitting_members data.
        Unlike member_count_intern (still manual: interns aren't tracked
        as sitting_members entries at all)."""
        return len(self.filled_positions)

    # Below this many events in the current semester, "auto" visibility
    # hides the calendar rather than showing a mostly-empty grid.
    CALENDAR_AUTO_MIN_EVENTS = 4

    def get_template(self, request, *args, **kwargs):
        """?calendar_partial=1 (union_calendar.js's Previous/Next fetch)
        renders just the calendar panel, no page chrome -- avoids a full
        reload, which on this site loses scroll position (html/body is its
        own scroll box, see elements.css; window.scrollY never reflects it,
        so a reload has nothing reliable to restore scroll from). Doesn't
        re-check "auto" mode's event count here -- if this URL is being
        fetched at all, the calendar was already showing when the page
        that holds the link was rendered, so only calendar_visibility
        being explicitly "never" is worth a cheap check before get_context
        makes the real (count-aware) decision."""
        if request.GET.get("calendar_partial") and self.calendar_visibility != "never":
            return "info_articles/partials/union_calendar_panel.html"
        return super().get_template(request, *args, **kwargs)

    def get_context(self, request, *args, **kwargs):
        """Add upcoming_events (live, still-upcoming EventPages tagging
        this union, grouped by month into upcoming_event_month_groups for
        the template -- same events/partials/event_month_groups.html
        listing EventIndexPage uses) and union_calendar (this week's events
        on the reusable week-calendar grid, navigable via ?calendar_date=).
        The two query helpers are imported locally: event.queries imports
        EventPage, which imports the article models this file belongs to.
        The calendar/date helpers import nothing, so they load normally at
        the top -- see docs/claude_context/article_unions.md."""
        context = super().get_context(request, *args, **kwargs)
        from ..event.queries import events_for_union_between, upcoming_events_for_union

        context["upcoming_events"] = upcoming_events_for_union(self)
        context["upcoming_event_month_groups"] = group_events_by_month(
            context["upcoming_events"]
        )

        # Needed either way: "auto" uses its count to decide visibility,
        # and (once shown) every mode uses it to fix the calendar's hour
        # axis for the whole semester.
        semester_start, semester_end = semester_bounds(timezone.localdate())
        semester_events = events_for_union_between(self, semester_start, semester_end)

        if self.calendar_visibility == "always":
            show_calendar = True
        elif self.calendar_visibility == "never":
            show_calendar = False
        else:
            show_calendar = len(semester_events) > self.CALENDAR_AUTO_MIN_EVENTS

        context["union_calendar"] = None
        if show_calendar:
            calendar_date_param = request.GET.get("calendar_date")
            try:
                calendar_date = (
                    date.fromisoformat(calendar_date_param)
                    if calendar_date_param
                    else timezone.localdate()
                )
            except ValueError:
                calendar_date = timezone.localdate()

            monday, sunday = week_bounds(calendar_date)
            week_events = events_for_union_between(self, monday, sunday)
            day_range = [monday + timedelta(days=i) for i in range(7)]

            # One fixed hour axis for every week this semester, derived
            # from this union's own earliest/latest timed event in it --
            # so paging through weeks doesn't reshuffle the grid's hours
            # each time (a 9:00-01:00 fallback, not the semester's own
            # full span, is used when this union has nothing timed
            # scheduled at all this semester to derive a range from).
            hour_range = hour_range_for_events(semester_events) or (9, 25)

            context["union_calendar"] = {
                "grid": build_calendar_days(
                    week_events, day_range=day_range, hour_range=hour_range
                ),
                # Raw dates, not a pre-built label string -- formatted with
                # Django's |date filter in the template so it stays locale-aware
                # (nb/en), same convention as event_list-style dates elsewhere.
                "week_start": monday,
                "week_end": sunday,
                # union_calendar.js intercepts clicks on these and fetches
                # &calendar_partial=1 instead of following them.
                "prev_url": f"?calendar_date={(monday - timedelta(days=7)).isoformat()}",
                "next_url": f"?calendar_date={(monday + timedelta(days=7)).isoformat()}",
            }
        return context


# Model for the category listing all student unions
class StudentUnionCategoryPage(
    EditorModeMixin, BannerStyleMixin, TranslationWarningMixin, Page
):  # pylint: disable=too-many-ancestors
    """A category page whose only children are student union pages."""

    template = "info_articles/pages/studentunion_category_page.html"

    intro = RichTextField(blank=True)
    general_info = RichTextField(
        blank=True,
        help_text="Optional -- a short paragraph of general information about student unions, shown below the intro.",
    )

    # Editor-curated groupings shown above the automatic "All unions"
    # listing -- see docs/claude_context/article_unions.md.
    union_groups = StreamField(
        [
            ("group", union_group_block()),
            (
                "row",
                blocks.StructBlock(
                    [
                        (
                            "title",
                            blocks.CharBlock(
                                required=False,
                                help_text="Optional -- a heading shown above the whole row, e.g. 'Foreninger'.",
                            ),
                        ),
                        (
                            "groups",
                            blocks.ListBlock(
                                union_group_block(),
                                help_text="Union groups to place side by side in this row.",
                            ),
                        ),
                    ],
                    icon="grip",
                    label="Row of union groups",
                ),
            ),
        ],
        use_json_field=True,
        blank=True,
        help_text=(
            "Optional -- organize unions into titled groups, standalone or "
            "side by side in a row. Every union also always appears in "
            "the 'All unions' listing below, regardless of grouping."
        ),
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("general_info"),
        FieldPanel("union_groups"),
    ]

    parent_page_types = ["ifi_home_app.ArticleIndexPage", "ifi_home_app.CategoryPage"]
    subpage_types = ["ifi_home_app.UnionPage"]

    def get_context(self, request, *args, **kwargs):
        """Split live unions into active/retired/unknown, plus automatic
        program_unions/other_unions groupings. See
        docs/claude_context/article_unions.md."""
        context = super().get_context(request, *args, **kwargs)
        context["can_edit_style"] = self.can_edit_in_editor_mode(request.user)
        context["can_sync_mirrored_page"] = self.can_sync_mirrored_page(request.user)
        context["translation_nudge"] = self.translation_nudge(request.user)
        unions = (
            UnionPage.objects.child_of(self)
            .live()
            .filter(locale=Locale.get_active())
            .order_by("title")
        )
        active_unions = unions.filter(status="active")
        context["active_unions"] = active_unions
        context["retired_unions"] = unions.filter(status="retired")
        context["unknown_unions"] = unions.filter(status="unknown")

        curated_ids = set()
        for block in self.union_groups:
            if block.block_type == "row":
                for group in block.value["groups"]:
                    curated_ids.update(
                        item["union"].id for item in group["unions"] if item["union"]
                    )
            elif block.block_type == "group":
                curated_ids.update(
                    item["union"].id for item in block.value["unions"] if item["union"]
                )

        context["program_unions"] = active_unions.filter(union_type="program")
        context["other_unions"] = active_unions.exclude(id__in=curated_ids).exclude(
            union_type="program"
        )
        return context
