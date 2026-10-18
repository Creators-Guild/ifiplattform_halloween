# pylint: disable=C0114,C0115,C0116
import tempfile
from pathlib import Path
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape
from django.utils import translation

from study_app import jokes
from study_app.jokes import all_jokes


class StudyJokePageTests(TestCase):
    """While study_app is under development, every /study/ path shows the
    joke page with one of all_jokes()."""

    def test_shows_a_joke_on_any_study_path(self):
        with translation.override("en"):
            for url in [reverse("study_home"), reverse("study_home") + "anything/"]:
                response = self.client.get(url)
                self.assertContains(response, "Ahaha, no.")
                self.assertTrue(
                    any(
                        escape(str(joke)) in response.content.decode()
                        for joke in all_jokes()
                    )
                )

    def test_joke_files_are_read(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder / "joke_01.txt").write_text("  A file joke.\n", encoding="utf-8")
            (folder / "joke_02.txt").write_text("\n", encoding="utf-8")
            (folder / "joke_03.txt").write_bytes(b"\xff\xfe broken")
            (folder / "README.md").write_text("not a joke", encoding="utf-8")
            with mock.patch.object(jokes, "JOKE_FILES_DIR", folder):
                self.assertEqual(jokes.file_jokes(), ["A file joke."])
                self.assertIn("A file joke.", all_jokes())

    def test_joke_number_shows_that_file(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder / "joke_05.txt").write_text("Number five.\n", encoding="utf-8")
            with mock.patch.object(jokes, "JOKE_FILES_DIR", folder):
                self.assertContains(self.client.get(reverse("study_home") + "?joke=05"), "Number five.")
                self.assertContains(self.client.get(reverse("study_home") + "?joke=5"), "Number five.")
                self.assertEqual(self.client.get(reverse("study_home") + "?joke=../x").status_code, 200)

    def test_excuse_api_url_comes_before_the_joke_page(self):
        response = self.client.get(reverse("study_excuse_api"))
        self.assertEqual(response["Content-Type"], "application/json")
