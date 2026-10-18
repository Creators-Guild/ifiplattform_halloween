# pylint: disable=C0114,C0115,C0116
import io

from django.core.management import call_command
from django.test import TestCase

from halloween_app.management.commands.halloween_stats import spooky_counts


class HalloweenStatsTests(TestCase):
    def test_counts_spooky_words(self):
        counts = spooky_counts("Ghost! A ghost and a PUMPKIN")
        self.assertEqual(counts["ghost"], 2)
        self.assertEqual(counts["pumpkin"], 1)

    def test_ignores_other_words(self):
        self.assertEqual(sum(spooky_counts("Just a normal Tuesday").values()), 0)

    def test_runs_on_an_empty_database(self):
        out = io.StringIO()
        call_command("halloween_stats", stdout=out)
        self.assertIn("Suspicious", out.getvalue())
