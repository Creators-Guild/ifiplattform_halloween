"""Event seeding: the top-level EVENT_SPECS events, plus Fadderuke's own
full Mon-Fri sub-event programme (which also seeds the unions it references)."""

from datetime import datetime, timedelta

from django.utils import timezone
from django.utils.text import slugify

from ifi_home_app.models import EventIndexPage, EventPage
from ifi_home_app.models.article_models import UnionPage
from ifi_home_app.translation import english_urls

from .constants import (
    EVENT_SPECS,
    FADDERUKE_HIGHLIGHTED_TITLES,
    FADDERUKE_LEGEND,
    FADDERUKE_SUB_EVENT_SPECS,
    FADDERUKE_SUB_EVENT_UNIONS,
    NAVET_COMPANY_PRESENTATION_COMPANIES,
    NAVET_COMPANY_PRESENTATION_END_TIME,
    NAVET_COMPANY_PRESENTATION_LOCATION,
    NAVET_COMPANY_PRESENTATION_TIME,
    NAVET_COMPANY_PRESENTATION_WEEKS,
)


class EventSeedMixin:
    def _seed_events(self, artikkler, nb_locale, seed_image):
        event_index = self._get_or_create_page(
            artikkler,
            EventIndexPage,
            "Arrangementer",
            nb_locale,
        )
        self._translate_page(event_index)

        today = timezone.now().date()
        fadderuke = None
        for title, event_type, offset_days, time_str, end_offset_days in EVENT_SPECS:
            # Fadderuke always starts next Monday, not EVENT_SPECS's plain
            # offset -- see docs/claude_context/seed_dev_data.md.
            if title == "Fadderuke":
                event_date = today + timedelta(days=(7 - today.weekday()) % 7)
            else:
                event_date = today + timedelta(days=offset_days)
            event = self._get_or_create_page(
                event_index,
                EventPage,
                title,
                nb_locale,
                event_type=event_type,
                event_date=event_date,
                event_time=(
                    datetime.strptime(time_str, "%H:%M").time() if time_str else None
                ),
                end_date=(
                    event_date + timedelta(days=end_offset_days)
                    if end_offset_days
                    else None
                ),
            )
            if title == "Fadderuke":
                # Not translated yet -- _seed_fadderuke_sub_events below
                # translates it itself, at the right point in the sequence.
                fadderuke = event
            else:
                self._translate_page(event)

        self._seed_fadderuke_sub_events(fadderuke, nb_locale, seed_image)
        self._seed_navet_company_presentations(event_index, nb_locale)

    def _seed_fadderuke_sub_events(self, fadderuke, nb_locale, seed_image):
        """Fills Fadderuke with a full Mon-Fri programme (see
        FADDERUKE_SUB_EVENT_SPECS) and its own calendar-color legend, so
        EventPage.calendar_days has a realistic week to lay out instead of
        just the lone parent event."""
        if not fadderuke.calendar_legend:
            fadderuke.calendar_legend = [
                ("entry", {"color": color, "label": label})
                for color, label in FADDERUKE_LEGEND
            ]
            fadderuke.save_revision().publish()

        unions = self._seed_fadderuke_unions(nb_locale, seed_image)

        # Fadderstyret hosts the whole week -- see
        # docs/claude_context/seed_dev_data.md.
        if not fadderuke.related_unions:
            fadderuke.related_unions = [
                ("union", {"union": unions["Fadderstyret"], "role": "host"}),
            ]
            fadderuke.save_revision().publish()

        # Must happen before any sub-event below is translated -- see
        # docs/claude_context/seed_dev_data.md before reordering this.
        self._translate_page(fadderuke)

        for (
            day_offset,
            title,
            event_type,
            start,
            end,
            color,
        ) in FADDERUKE_SUB_EVENT_SPECS:
            event_date = fadderuke.event_date + timedelta(days=day_offset)
            sub_event = self._get_or_create_page(
                fadderuke,
                EventPage,
                title,
                nb_locale,
                event_type=event_type,
                event_date=event_date,
                event_time=datetime.strptime(start, "%H:%M").time(),
                event_end_time=datetime.strptime(end, "%H:%M").time(),
                calendar_color=color,
                show_on_homepage=False,
                is_highlighted=title in FADDERUKE_HIGHLIGHTED_TITLES,
            )

            union_roles = FADDERUKE_SUB_EVENT_UNIONS.get(title)
            if union_roles and not sub_event.related_unions:
                sub_event.related_unions = [
                    ("union", {"union": unions[union_title], "role": role})
                    for union_title, role in union_roles
                ]
                sub_event.save_revision().publish()

            self._translate_page(sub_event)

    def _seed_navet_company_presentations(self, event_index, nb_locale):
        """Recurring Tue/Thu "company presentation" EventPages for Navet --
        its real Peoply events were removed, so sync_peoply_events no
        longer produces any for it; this keeps its calendar looking
        realistic in local dev regardless. external_source/external_uid
        are left blank (unlike a real synced event) since these aren't
        actually from Peoply. Requires _seed_fadderuke_unions (called from
        _seed_fadderuke_sub_events, above) to have already created Navet."""
        navet = UnionPage.objects.get(title="Navet", locale=nb_locale)
        companies = NAVET_COMPANY_PRESENTATION_COMPANIES
        event_time = datetime.strptime(NAVET_COMPANY_PRESENTATION_TIME, "%H:%M").time()
        event_end_time = datetime.strptime(
            NAVET_COMPANY_PRESENTATION_END_TIME, "%H:%M"
        ).time()

        today = timezone.now().date()
        last_date = today + timedelta(weeks=NAVET_COMPANY_PRESENTATION_WEEKS)
        dates = []
        day = today + timedelta(days=1)
        while day <= last_date:
            if day.weekday() in (1, 3):  # Tuesday, Thursday
                dates.append(day)
            day += timedelta(days=1)

        for i, event_date in enumerate(dates):
            company = companies[i % len(companies)]
            title = f"Bedriftspresentasjon med {company}"
            slug = f"bedriftspresentasjon-{slugify(company)}-{event_date.isoformat()}"
            event = self._get_or_create_page(
                event_index,
                EventPage,
                title,
                nb_locale,
                slug=slug,
                event_type="company",
                event_date=event_date,
                event_time=event_time,
                event_end_time=event_end_time,
                location=NAVET_COMPANY_PRESENTATION_LOCATION,
                intro=(
                    f"<p>Velkommen til bedriftspresentasjon med {company}!</p>"
                    f"<p>Arrangør: {company}<br>Mat: Pizza<br>Språk: Norsk<br/>"
                    f"Aldersgrense: 18<br>Plasser: 40</p>"
                    f"<p>Bli med for en uformell presentasjon, etterfulgt av god mat og drikke.</p>"
                ),
            )
            if not event.related_unions:
                event.related_unions = [("union", {"union": navet, "role": "host"})]
                event.save_revision().publish()
            if english_urls.english_slug(event) is None:
                english_urls.set_english_slug(
                    event,
                    f"company-presentation-{slugify(company)}-{event_date.isoformat()}",
                    "deepl",
                    redirect=False,
                )
            self._translate_page(event)
