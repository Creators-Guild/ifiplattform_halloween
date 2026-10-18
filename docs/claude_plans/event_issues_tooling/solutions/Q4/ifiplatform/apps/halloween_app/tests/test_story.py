# pylint: disable=C0114,C0115,C0116
from django.test import SimpleTestCase

from halloween_app.views.story import FIELDS, tell_story

WORDS = {"name": "Kari", "place": "the 3rd floor", "food": "taco", "number": "13", "creature": "mummy", "sound": "BOO"}


class StoryTests(SimpleTestCase):
    def test_every_word_is_used(self):
        story = " ".join(tell_story(WORDS))
        for word in WORDS.values():
            self.assertIn(word, story)

    def test_a_missing_word_gives_no_story(self):
        self.assertIsNone(tell_story({**WORDS, "food": ""}))

    def test_at_least_three_paragraphs(self):
        self.assertGreaterEqual(len(tell_story(WORDS)), 3)

    def test_every_field_is_asked_for(self):
        self.assertEqual(len(FIELDS), len(WORDS))

    def test_curly_braces_in_a_word_dont_crash(self):
        self.assertIsNotNone(tell_story({**WORDS, "name": "{name}"}))
