"""Keeps the study page's joke files tidy: every file in joke_files/ that
isn't the README is a joke_NN.txt with one short joke, in UTF-8, and no
joke is there twice."""

# pylint: disable=C0115,C0116
import re

from django.test import SimpleTestCase

from study_app.jokes import JOKE_FILES_DIR, STUDY_JOKES

MAX_LENGTH = 200


def joke_files():
    return sorted(path for path in JOKE_FILES_DIR.iterdir() if path.name != "README.md")


class JokeFileTests(SimpleTestCase):
    def test_file_names(self):
        for path in joke_files():
            self.assertRegex(path.name, r"^joke_\d{2}\.txt$")

    def test_utf8_and_not_empty(self):
        for path in joke_files():
            with self.subTest(path.name):
                self.assertTrue(path.read_text(encoding="utf-8").strip())

    def test_short(self):
        for path in joke_files():
            with self.subTest(path.name):
                self.assertLessEqual(len(path.read_text(encoding="utf-8").strip()), MAX_LENGTH)

    def test_one_paragraph(self):
        for path in joke_files():
            with self.subTest(path.name):
                self.assertNotRegex(path.read_text(encoding="utf-8").strip(), r"\n\s*\n")

    def test_no_joke_twice(self):
        texts = [re.sub(r"\s+", " ", path.read_text(encoding="utf-8").strip().lower()) for path in joke_files()]
        texts += [str(joke).lower() for joke in STUDY_JOKES]
        self.assertEqual(len(texts), len(set(texts)))
