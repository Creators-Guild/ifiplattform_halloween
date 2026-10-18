# pylint: disable=C0114,C0115,C0116
from datetime import datetime, timezone

from django.test import SimpleTestCase

from halloween_app.moon_phase import phase, shadow_offset


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


class MoonPhaseTests(SimpleTestCase):
    def test_known_new_moon(self):
        moon_phase = phase(utc(2026, 10, 10, 12))
        self.assertLess(min(moon_phase, 1 - moon_phase), 0.05)

    def test_known_full_moon(self):
        self.assertAlmostEqual(phase(utc(2026, 10, 26, 4)), 0.5, delta=0.03)

    def test_phase_is_between_0_and_1(self):
        for day in range(1, 29):
            self.assertTrue(0 <= phase(utc(2026, 2, day)) < 1)

    def test_shadow(self):
        self.assertEqual(shadow_offset(0), 0)
        self.assertEqual(shadow_offset(0.25), -50)
        self.assertEqual(shadow_offset(0.5), -100)
        self.assertEqual(shadow_offset(0.75), 50)
