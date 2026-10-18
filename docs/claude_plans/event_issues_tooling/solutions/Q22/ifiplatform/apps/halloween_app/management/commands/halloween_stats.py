"""python manage.py halloween_stats: how spooky are the articles?"""

import re
from collections import Counter

from django.core.management.base import BaseCommand
from django.utils.html import strip_tags

from ifi_home_app.models import ArticlePage

SPOOKY_WORDS = ["ghost", "spøkelse", "pumpkin", "gresskar", "bat", "flaggermus", "witch", "heks"]


def spooky_counts(text):
    """How often each spooky word appears in text, as a Counter."""
    words = re.findall(r"\w+", text.lower())
    return Counter(word for word in words if word in SPOOKY_WORDS)


class Command(BaseCommand):
    help = "Counts spooky words in the titles and intros of the live articles."

    def handle(self, *args, **options):
        total = Counter()
        spookiest, most = None, 0
        for page in ArticlePage.objects.live():
            counts = spooky_counts(f"{page.title} {strip_tags(page.intro)}")
            total += counts
            if sum(counts.values()) > most:
                spookiest, most = page, sum(counts.values())
        for word, count in total.most_common():
            self.stdout.write(f"{word:<12}{count}")
        if spookiest:
            self.stdout.write(f'Spookiest article: "{spookiest.title}" ({most} spooky words)')
        else:
            self.stdout.write("No spooky words anywhere. Suspicious.")
