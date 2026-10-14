"""The event page tree: EventIndexPage -> EventPage.

Design rationale/history: docs/claude_context/event_models.md"""

from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page

from ifi_home_app.models.article_models import (
    HEX_COLOR_VALIDATOR,
    TranslationWarningMixin,
    article_card_block,
)

from .blocks import (
    calendar_legend_entry_block,
    event_union_block,
    location_map_link_block,
)
from .calendar_layout import build_calendar_days
from .constants import (
    EVENT_CALENDAR_COLOR_CHOICES,
    EVENT_TYPE_CHOICES,
    SITE_TIMEZONE,
    UNION_ROLE_CHOICES,
)
from .dates import group_events_by_month
from .peoply import PEOPLY_SYNCED_FIELDS
from ...translation.english_overlay import EnglishPreviewMixin


class EventPageTag(TaggedItemBase):
    """Through-model for EventPage.info_tags. Free-text tags with
    autocomplete from previously-used ones, not a fixed choices list."""

    content_object = ParentalKey(
        "EventPage", on_delete=models.CASCADE, related_name="tagged_items"
    )


class EventPageForm(WagtailAdminPageForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.external_source != "peoply":
            return
        for name in PEOPLY_SYNCED_FIELDS:
            field = self.fields.get(name)
            if field is None:
                continue
            field.disabled = True
            field.help_text = _("Synced from Peoply -- edit it on Peoply instead.")


class EventIndexPage(EnglishPreviewMixin, TranslationWarningMixin, Page):
    """Landing page listing all events."""

    template = "events/event_index_page.html"
    translated_fields = ["intro"]

    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    subpage_types = ["ifi_home_app.EventPage"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        events = list(
            EventPage.objects.child_of(self).live().order_by("event_date", "event_time")
        )
        today = timezone.localdate()
        # Same "still going" rule as is_happening_now: an event only counts
        # as past once its last day (end_date if set, else event_date) is
        # behind us -- a week-long event isn't "past" on day 2. An archived
        # event (dropped from Peoply, kept by an admin -- see
        # PeoplyRemovedEvent) is always past, whatever its date.
        upcoming_events = [
            e
            for e in events
            if not e.is_archived and (e.end_date or e.event_date) >= today
        ]
        past_events = [
            e for e in events if e.is_archived or (e.end_date or e.event_date) < today
        ]

        context["events"] = events
        context["month_groups"] = group_events_by_month(upcoming_events)
        # Most-recently-past month first, since that's the one someone
        # skimming "past events" is most likely looking for.
        context["past_month_groups"] = group_events_by_month(
            list(reversed(past_events))
        )
        context["current_semester_year"] = today.year
        context["is_spring_semester"] = today.month <= 6
        return context


class EventPage(EnglishPreviewMixin, TranslationWarningMixin, Page):
    """A single event -- covers dated events, week-long events (via
    end_date), and deadlines through the same shape."""

    template = "events/event_page.html"
    translated_fields = ["location", "intro", "location_map_links", "calendar_legend"]

    event_type = models.CharField(
        max_length=20, choices=EVENT_TYPE_CHOICES, default="other"
    )
    event_date = models.DateField()
    event_time = models.TimeField(
        null=True, blank=True
    )  # blank = "no specific time" (e.g. week-long Fadderuke)
    event_end_time = models.TimeField(
        null=True, blank=True
    )  # only used to size this event's block in calendar_days
    calendar_color = models.CharField(
        max_length=20,
        choices=EVENT_CALENDAR_COLOR_CHOICES,
        blank=True,
        help_text="Optional -- overrides the automatic color of this event's block in a parent event's week-calendar view.",
    )
    calendar_color_custom = models.CharField(
        max_length=7,
        blank=True,
        validators=[HEX_COLOR_VALIDATOR],
        help_text="Used only when Calendar color above is set to Custom.",
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Optional -- for events spanning more than one day.",
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional -- where the event takes place, e.g. a building or room name.",
    )
    location_map_links = StreamField(
        [("map_link", location_map_link_block())],
        use_json_field=True,
        blank=True,
        help_text="Optional -- one or more titled links to a map (e.g. Google Maps) for this event's location(s).",
    )
    location_articles = StreamField(
        [("article", article_card_block())],
        use_json_field=True,
        blank=True,
        help_text="Optional -- links to existing articles with more info about this event's location(s).",
    )
    intro = RichTextField(blank=True)
    show_on_homepage = models.BooleanField(
        default=True,
        help_text="Whether this event can appear in the homepage's upcoming-events box.",
    )
    is_highlighted = models.BooleanField(
        default=False,
        help_text="For a sub-event: show it in its parent event's homepage dropdown.",
    )

    # Set by sync_peoply_events ("peoply" + Peoply's own event id) -- ""
    # means manually created. Peoply is the source of truth for
    # PEOPLY_SYNCED_FIELDS on these, see EventPageForm.
    external_source = models.CharField(max_length=20, blank=True)
    external_uid = models.CharField(max_length=200, blank=True)
    is_archived = models.BooleanField(
        default=False,
        help_text="Removed from Peoply, but kept visible under previous events only.",
    )

    related_unions = StreamField(
        [("union", event_union_block())],
        use_json_field=True,
        blank=True,
        help_text="Optional -- student unions involved in this event, and their role.",
    )
    calendar_legend = StreamField(
        [("entry", calendar_legend_entry_block())],
        use_json_field=True,
        blank=True,
        help_text='Optional -- explains what each sub-event calendar color means (e.g. "Blue = Study-relevant"), shown above the week-calendar.',
    )
    peoply_url = models.URLField(
        blank=True,
        help_text="Optional -- link to this event's page on Peoply.",
    )
    signup_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Optional -- link to a signup/registration form for this event, if not using Peoply.",
    )
    info_tags = ClusterTaggableManager(
        through=EventPageTag,
        blank=True,
        help_text='Optional -- e.g. "Bachelor", "MN students", "Food served", "Alcohol-free".',
    )

    content_panels = Page.content_panels + [
        FieldPanel("event_type"),
        FieldPanel("event_date"),
        FieldPanel("event_time"),
        FieldPanel("event_end_time"),
        FieldPanel("calendar_color"),
        FieldPanel("calendar_color_custom"),
        FieldPanel("end_date"),
        FieldPanel("location"),
        FieldPanel("location_map_links"),
        FieldPanel("location_articles"),
        FieldPanel("intro"),
        FieldPanel("show_on_homepage"),
        FieldPanel("is_highlighted"),
        FieldPanel("related_unions"),
        FieldPanel("calendar_legend"),
        FieldPanel("peoply_url"),
        FieldPanel("signup_url"),
        FieldPanel("info_tags"),
    ]

    base_form_class = EventPageForm

    parent_page_types = ["ifi_home_app.EventIndexPage", "ifi_home_app.EventPage"]
    subpage_types = ["ifi_home_app.EventPage"]

    @classmethod
    def can_create_at(cls, parent):
        """Sub-events can't have sub-events of their own."""
        if not super().can_create_at(parent):
            return False
        if isinstance(parent, EventPage):
            return not isinstance(parent.get_parent().specific, EventPage)
        return True

    @property
    def is_happening_now(self):
        """True on any day this event is in progress (event_date through
        end_date inclusive)."""
        today = timezone.localdate()
        return self.event_date <= today <= (self.end_date or self.event_date)

    @property
    def signs_up_on_peoply(self):
        """Whether signing up means clicking through to Peoply itself
        rather than to an external form -- true for a Peoply-sourced event
        with no signup_url. See docs/claude_context/event_models.md."""
        return self.external_source == "peoply" and not self.signup_url

    @property
    def time_tag(self):
        """ "today" or "tomorrow" when the event falls on one of those, else
        None -- at most one applies, nearest first."""
        if self.is_happening_now:
            return "today"
        if self.event_date == timezone.localdate() + timedelta(days=1):
            return "tomorrow"
        return None

    @cached_property
    def sub_events(self):
        return (
            EventPage.objects.child_of(self).live().order_by("event_date", "event_time")
        )

    @cached_property
    def sub_event_count(self):
        """How many sub-events this event has -- a COUNT query, kept out of
        the templates that only need the number."""
        return self.sub_events.count()

    @property
    def location_article_pages(self):
        """The linked ArticlePages (specific), skipping deleted ones."""
        return [
            entry.value["article"].specific
            for entry in self.location_articles
            if entry.value["article"] is not None
        ]

    @cached_property
    def all_related_unions(self):
        """This event's related_unions plus every sub_event's, deduped by
        union keeping the highest-priority role, each made `.specific` here
        rather than in every template. See docs/claude_context/event_models.md
        for the host-capping rule."""
        role_priority = {"host": 0, "collaborator": 1, "contributor": 2}
        best_by_union = {}

        def add_entries(entries, cap_host):
            for entry in entries:
                union = entry.value["union"]
                if union is None:
                    continue
                role = entry.value["role"]
                if cap_host and role == "host":
                    role = "collaborator"
                key = union.pk
                if (
                    key not in best_by_union
                    or role_priority[role] < role_priority[best_by_union[key][0]]
                ):
                    best_by_union[key] = (role, union)

        add_entries(self.related_unions, cap_host=False)
        for sub_event in self.sub_events:
            add_entries(sub_event.related_unions, cap_host=True)

        role_labels = dict(UNION_ROLE_CHOICES)
        return [
            {
                "role": role,
                "role_label": role_labels[role],
                "union": union.specific,
            }
            for role, union in best_by_union.values()
        ]

    @property
    def host_unions(self):
        """all_related_unions entries running the event -- shown in their
        own row above everyone else on the event page."""
        return [entry for entry in self.all_related_unions if entry["role"] == "host"]

    @property
    def supporting_unions(self):
        """all_related_unions entries helping rather than running it
        (contributor/collaborator)."""
        return [entry for entry in self.all_related_unions if entry["role"] != "host"]

    # Beyond this many union tags, the homepage events box collapses the
    # rest into a "+N" disclosure rather than letting one event's tags
    # push the whole list item taller than the ones around it.
    UNION_TAGS_SHOWN = 2

    @property
    def visible_union_tags(self):
        """all_related_unions entries shown inline on the events box."""
        return self.all_related_unions[: self.UNION_TAGS_SHOWN]

    @property
    def extra_union_tags(self):
        """all_related_unions entries hidden behind the "+N" disclosure."""
        return self.all_related_unions[self.UNION_TAGS_SHOWN :]

    @cached_property
    def highlighted_sub_events(self):
        """Today's sub-event(s) if any are scheduled today, else the
        curated is_highlighted set."""
        today_events = self.sub_events.filter(event_date=timezone.localdate())
        if today_events.exists():
            return today_events
        return self.sub_events.filter(is_highlighted=True)

    @cached_property
    def calendar_days(self):
        """This event's sub_events laid out for a week-calendar view -- see
        docs/claude_context/event_models.md for the full layout algorithm."""
        return build_calendar_days(self.sub_events)
