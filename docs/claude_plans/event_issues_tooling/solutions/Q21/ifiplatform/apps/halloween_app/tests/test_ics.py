# pylint: disable=C0114,C0115,C0116
from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from halloween_app.views.ics import ics_text


class IcsTests(TestCase):
    def test_timed_event(self):
        text = ics_text("x@test", "Pumpkin carving", date(2026, 10, 30), time(18, 0), end_time=time(21, 30))
        self.assertIn("DTSTART;TZID=Europe/Oslo:20261030T180000", text)
        self.assertIn("DTEND;TZID=Europe/Oslo:20261030T213000", text)
        self.assertIn("SUMMARY:Pumpkin carving", text)

    def test_all_day_event_ends_the_next_day(self):
        text = ics_text("x@test", "Halloween", date(2026, 10, 31))
        self.assertIn("DTSTART;VALUE=DATE:20261031", text)
        self.assertIn("DTEND;VALUE=DATE:20261101", text)

    def test_commas_are_escaped(self):
        text = ics_text("x@test", "Ghosts, bats; and more", date(2026, 10, 31))
        self.assertIn("SUMMARY:Ghosts\\, bats\\; and more", text)

    def test_lines_end_with_crlf(self):
        self.assertTrue(ics_text("x@test", "A", date(2026, 10, 31)).endswith("END:VCALENDAR\r\n"))

    def test_unknown_event_is_404(self):
        self.assertEqual(self.client.get(reverse("halloween_event_ics", args=[999999])).status_code, 404)
