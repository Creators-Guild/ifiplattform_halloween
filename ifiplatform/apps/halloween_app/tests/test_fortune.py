# pylint: disable=C0114,C0115,C0116
from django.test import SimpleTestCase

from halloween_app.views.fortune import FORTUNES, pick_fortune


class FortuneTests(SimpleTestCase):
    def test_gives_a_fortune(self):
        self.assertIn(pick_fortune("Kari"), FORTUNES)

    def test_same_name_same_fortune(self):
        self.assertEqual(pick_fortune("Kari"), pick_fortune("  KARI "))

    def test_enough_fortunes(self):
        # TODO: check that there are at least 8 fortunes
        self.assertGreaterEqual(len(FORTUNES), 8)