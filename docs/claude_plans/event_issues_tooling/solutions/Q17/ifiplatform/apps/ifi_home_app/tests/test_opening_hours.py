# pylint: disable=C0114,C0115,C0116
from datetime import datetime

from django.test import SimpleTestCase

from ifi_home_app.opening_hours import OSLO, is_open

DAY = {"hours": [("08:00", "16:00")] * 5 + [None, None]}
NIGHT = {"hours": [("20:00", "02:00")] * 5 + [None, None]}


def at(day, time):
    """day 19 is a Monday (October 2026)."""
    hour, minute = map(int, time.split(":"))
    return datetime(2026, 10, day, hour, minute, tzinfo=OSLO)


class IsOpenTests(SimpleTestCase):
    def test_normal_hours(self):
        self.assertTrue(is_open(DAY, at(19, "12:00")))
        self.assertFalse(is_open(DAY, at(19, "07:59")))
        self.assertTrue(is_open(DAY, at(19, "08:00")))
        self.assertFalse(is_open(DAY, at(19, "16:00")))

    def test_closed_all_day(self):
        self.assertFalse(is_open(DAY, at(24, "12:00")))

    def test_open_past_midnight(self):
        self.assertTrue(is_open(NIGHT, at(19, "23:30")))
        self.assertTrue(is_open(NIGHT, at(20, "01:30")))
        self.assertFalse(is_open(NIGHT, at(20, "02:00")))
        self.assertFalse(is_open(NIGHT, at(19, "12:00")))

    def test_friday_night_runs_into_saturday(self):
        self.assertTrue(is_open(NIGHT, at(24, "01:00")))
        self.assertFalse(is_open(NIGHT, at(24, "21:00")))

    def test_sunday_night_is_closed_on_monday_morning(self):
        self.assertFalse(is_open(NIGHT, at(19, "01:00")))
