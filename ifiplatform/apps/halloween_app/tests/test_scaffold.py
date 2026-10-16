# pylint: disable=C0114,C0115,C0116
import tempfile
from pathlib import Path

from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from halloween_app import board
from halloween_app.pages import PAGES


class HalloweenCornerTests(TestCase):
    """The organisers' scaffold: every page opens, before and after the event
    issues fill them in. Issue tests go in their own files."""

    def setUp(self):
        self.enterContext(translation.override("en"))

    def test_hub_links_every_page(self):
        response = self.client.get(reverse("halloween_hub"))
        for slug, _emoji, title, _text in PAGES:
            self.assertContains(response, reverse(f"halloween_{slug}"))
            self.assertContains(response, title)

    def test_every_page_opens(self):
        for slug, *_rest in PAGES:
            self.assertEqual(self.client.get(reverse(f"halloween_{slug}")).status_code, 200, slug)

    def test_forms_work_before_the_issues_are_done(self):
        for name, query in [
            ("halloween_fortune", "?name=Kari"),
            ("halloween_spooky_name", "?name=Kari"),
            ("halloween_potion", "?ingredient=pumpkin&brew=1"),
        ]:
            self.assertEqual(self.client.get(reverse(name) + query).status_code, 200, name)

    def test_404_preview(self):
        self.assertEqual(self.client.get(reverse("halloween_404_preview")).status_code, 404)

    def test_board_shows_the_example_notes(self):
        kinds = {note.kind for note in board.load_notes()}
        self.assertEqual(kinds, set(board.KINDS))
        response = self.client.get(reverse("halloween_board"))
        self.assertContains(response, "Here lies printf debugging")
        self.assertContains(response, 'class="note note--warning"')

    def test_note_format(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder / "rule_01.txt").write_text("Title\nLine one\nLine two\n— Me\n", encoding="utf-8")
            (folder / "notes.txt").write_text("not a kind\n", encoding="utf-8")
            (folder / "warning_01.txt").write_bytes(b"\xff\xfe broken")
            original = board.NOTES_DIR
            board.NOTES_DIR = folder
            try:
                notes = board.load_notes()
            finally:
                board.NOTES_DIR = original
        self.assertEqual(len(notes), 1)
        note = notes[0]
        self.assertEqual(
            (note.kind, note.title, note.text, note.signature),
            ("rule", "Title", "Line one\nLine two", "Me"),
        )
        self.assertIn(note.tilt, range(-3, 4))
