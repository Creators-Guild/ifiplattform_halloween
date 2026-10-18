# pylint: disable=C0114,C0115,C0116
from django.test import SimpleTestCase

from halloween_app.views.spooky_name import FIRST_PARTS, LAST_PARTS, spooky_name


class SpookyNameTests(SimpleTestCase):
    def test_keeps_the_name(self):
        self.assertIn("Kari", spooky_name("Kari"))

    def test_same_name_same_result(self):
        self.assertEqual(spooky_name("Kari"), spooky_name("Kari"))

    def test_uses_the_lists(self):
        result = spooky_name("Kari")
        self.assertTrue(any(result.startswith(part) for part in FIRST_PARTS))
        self.assertTrue(any(result.endswith(part) for part in LAST_PARTS))
