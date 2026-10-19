"""Keeps the study page's joke files tidy: every file in joke_files/ that
isn't the README is a joke_NN.txt with one short joke, in UTF-8, and no
joke is there twice."""

# pylint: disable=C0115,C0116
from django.test import SimpleTestCase

from study_app.jokes import JOKE_FILES_DIR, STUDY_JOKES

MAX_LENGTH = 200


def joke_files():
    return sorted(path for path in JOKE_FILES_DIR.iterdir() if path.name != "README.md")


class JokeFileTests(SimpleTestCase):
    def test_jokes_exist(self):
        self.assertNotEqual(0, len(joke_files()))

    def test_file_names(self):
        for path in joke_files():
            self.assertRegex(path.name, r"^joke_\d{2}\.txt$")

    def test_non_empty_utf8(self):
        for path in joke_files():
            with self.subTest(path.name), open(
                JOKE_FILES_DIR / path.name, "r", encoding="utf-8"
            ) as f:
                self.assertNotEqual("", f.read().strip())

    def test_short(self):
        for path in joke_files():
            with self.subTest(path.name), open(
                JOKE_FILES_DIR / path.name, "r", encoding="utf-8"
            ) as f:
                self.assertLessEqual(len(f.read()), MAX_LENGTH)

    def test_single_paragraph(self):
        for path in joke_files():
            with self.subTest(path.name), open(
                JOKE_FILES_DIR / path.name, "r", encoding="utf-8"
            ) as f:
                self.assertNotRegex(f.read(), r"\n\s*\n")

    def test_no_duplicates(self):
        seen: set[str] = set()
        for path in joke_files():
            with self.subTest(path.name), open(
                JOKE_FILES_DIR / path.name, "r", encoding="utf-8"
            ) as f:
                joke: str = f.read().strip()
                self.assertNotIn(joke, seen)
                seen.add(joke)
