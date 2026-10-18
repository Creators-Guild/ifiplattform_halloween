# pylint: disable=C0114,C0115,C0116
from django.test import SimpleTestCase

from halloween_app.fortune_names import clean_name


class CleanNameTests(SimpleTestCase):
    def test_norwegian_letters(self):
        self.assertEqual(clean_name("Åse"), "ase")
        self.assertEqual(clean_name("  Bjørn "), "bjorn")
        self.assertEqual(clean_name("Kæthe"), "kaethe")

    def test_accents(self):
        self.assertEqual(clean_name("René"), "rene")

    def test_emoji_is_dropped(self):
        self.assertEqual(clean_name("Kari🎃"), "kari")
