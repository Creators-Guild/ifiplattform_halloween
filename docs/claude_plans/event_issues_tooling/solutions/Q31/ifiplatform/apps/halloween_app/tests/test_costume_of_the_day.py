# pylint: disable=C0114,C0115,C0116
from datetime import date, timedelta

from django.test import SimpleTestCase

from halloween_app.costume_of_the_day import COSTUMES, costume_of_the_day


class CostumeOfTheDayTests(SimpleTestCase):
    def test_same_day_same_costume(self):
        self.assertEqual(costume_of_the_day(date(2026, 10, 31)), costume_of_the_day(date(2026, 10, 31)))

    def test_it_is_one_of_the_costumes(self):
        self.assertIn(costume_of_the_day(date(2026, 10, 19)), COSTUMES)

    def test_it_changes(self):
        start = date(2026, 10, 1)
        picks = {costume_of_the_day(start + timedelta(days=n)) for n in range(31)}
        self.assertGreater(len(picks), 1)
