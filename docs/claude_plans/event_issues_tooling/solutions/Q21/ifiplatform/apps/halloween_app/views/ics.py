"""Add an event to your calendar: an .ics file for one event page, which
every calendar app (Google, Outlook, Apple) can import."""

from datetime import datetime, timedelta, timezone

from django.http import Http404, HttpResponse

from ifi_home_app.models import EventPage


def ics_escape(text):
    """Commas, semicolons, backslashes and new lines need a \\ in front."""
    return (
        text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    )


def ics_text(uid, title, start_date, start_time=None, end_date=None, end_time=None, location="", url=""):
    """The .ics file for one event, as text. Without a start time it's an
    all-day event; times are Norwegian time."""
    if start_time:
        start = datetime.combine(start_date, start_time)
        if end_time:
            end = datetime.combine(end_date or start_date, end_time)
        else:
            end = start + timedelta(hours=2)
        when = [
            f"DTSTART;TZID=Europe/Oslo:{start:%Y%m%dT%H%M%S}",
            f"DTEND;TZID=Europe/Oslo:{end:%Y%m%dT%H%M%S}",
        ]
    else:
        last_day = end_date or start_date
        when = [
            f"DTSTART;VALUE=DATE:{start_date:%Y%m%d}",
            f"DTEND;VALUE=DATE:{last_day + timedelta(days=1):%Y%m%d}",
        ]
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Ifi Platform//Halloween corner//EN",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}",
        *when,
        f"SUMMARY:{ics_escape(title)}",
    ]
    if location:
        lines.append(f"LOCATION:{ics_escape(location)}")
    if url:
        lines.append(f"URL:{url}")
    lines += ["END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(lines) + "\r\n"


def event_ics_view(request, page_id):
    page = EventPage.objects.live().filter(id=page_id).first()
    if page is None:
        raise Http404("No such event")
    text = ics_text(
        uid=f"event-{page.id}@ifiplattform.no",
        title=page.title,
        start_date=page.event_date,
        start_time=page.event_time,
        end_date=page.end_date,
        end_time=page.event_end_time,
        location=page.location,
        url=page.get_full_url(request) or "",
    )
    response = HttpResponse(text, content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{page.slug}.ics"'
    return response
