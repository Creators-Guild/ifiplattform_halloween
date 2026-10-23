# pylint: disable=C0114,C0115,C0116
from django.test import SimpleTestCase

from halloween_app.views.potion import mix


class PotionTests(SimpleTestCase):
    def test_nothing_is_water(self):
        self.assertEqual(mix([]), "Just water. Spooky.")

    def test_order_does_not_matter(self):
        self.assertEqual(mix(["coffee", "bat_wing"]), mix(["bat_wing", "coffee"]))

    def test_everything_has_a_result(self):
        # Check that mix() of all six ingredients returns some text
        result = mix(["bat_wing", "pumpkin", "spider", "eyeball", "candy", "coffee"])
        self.assertTrue(isinstance(result, str))  # Ensure the result is a string
        self.assertTrue(len(result) > 0)  # Ensure the result is not an empty string