# pylint: disable=C0114,C0115,C0116
from datetime import date

from django.test import SimpleTestCase

from halloween_app.views.countdown import next_halloween


class NextHalloweenTests(SimpleTestCase):
    def test_before_halloween(self):
        self.assertEqual(next_halloween(date(2026, 10, 19)), date(2026, 10, 31))

    def test_on_halloween(self):
        self.assertEqual(next_halloween(date(2026, 10, 31)), date(2026, 10, 31))

    def test_after_halloween(self):
        self.assertEqual(next_halloween(date(2026, 11, 1)), date(2027, 10, 31))

    def test_new_years_eve(self):
        self.assertEqual(next_halloween(date(2026, 12, 31)), date(2027, 10, 31))
