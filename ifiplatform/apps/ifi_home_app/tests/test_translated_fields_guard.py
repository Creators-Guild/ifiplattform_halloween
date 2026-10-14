# pylint: disable=C0114,C0115,C0116
"""Automatic guards for the English overlay: every model declares
translated_fields, renaming a translated place can't silently orphan its
English, and wagtail-localize stays behind page_segments.py. See
docs/claude_context/translation_overlay.md."""

import ast
import json
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from wagtail.models import Locale, Page, TranslatableMixin

from ifi_home_app.models import ArticleIndexPage, ArticlePage, SegmentTranslation
from ifi_home_app.translation import page_segments, stored_translations
from ifi_home_app.translation.page_segments import SNAPSHOT_PATH, current_places

PROJECT = Path(settings.BASE_DIR)

ALLOWED_IMPORTERS = {"apps/ifi_home_app/translation/page_segments.py"}


def _project_models():
    return [
        model
        for model in apps.get_models()
        if model._meta.app_config.path.startswith(str(PROJECT))
    ]


class TranslatedFieldsDeclaredTests(SimpleTestCase):
    def test_every_page_type_and_snippet_declares_translated_fields(self):
        missing = [
            model.__name__
            for model in _project_models()
            if issubclass(model, (Page, TranslatableMixin))
            and "translated_fields" not in vars(model)
        ]
        self.assertEqual(
            missing,
            [],
            "These models have no translated_fields. Add a list of the fields "
            "with text for visitors, e.g. translated_fields = ['intro', 'body'], "
            "or translated_fields = [] if there are none. Leave out IDs, URLs, "
            "colours, choices and people's names.",
        )


class RenameProtectionTests(SimpleTestCase):
    def test_snapshot_matches_models(self):
        saved = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        current = current_places()
        if saved == current:
            return
        self.fail(_snapshot_message(saved, current))


def _snapshot_message(saved, current):
    lines = [
        "Translated places changed. Stored English is keyed by these places, "
        "so a rename without a fix orphans it (DeepL starts over, people's "
        "fixes are lost).",
        "",
    ]
    suggestions = []
    for label in sorted(set(saved) | set(current)):
        old, new = saved.get(label, {}), current.get(label, {})
        gone = {r: s for r, s in old.items() if r not in new}
        added = {r: s for r, s in new.items() if r not in old}
        model = label.split(".")[-1]
        for readable, stored in gone.items():
            lines.append(f"  gone: {model}: {readable}")
            if stored in new.values():
                continue  # only a block type name changed: nothing moves
            parent = readable.rsplit(" → ", 1)[0] if " → " in readable else ""
            for new_readable, new_stored in added.items():
                new_parent = (
                    new_readable.rsplit(" → ", 1)[0] if " → " in new_readable else ""
                )
                if new_parent == parent and new_stored not in old.values():
                    suggestions.append(
                        f'    rename_segment_path(apps, "{model}", "{stored}", "{new_stored}")'
                    )
        lines += [f"  new:  {model}: {readable}" for readable in added]
    lines += [
        "",
        "If you RENAMED a field, or a field inside a block, move the stored "
        "English in the migration that renames it:",
        "    from ifi_home_app.translation.stored_translations import rename_segment_path",
        "    migrations.RunPython(",
        "        lambda apps, schema_editor: (",
    ]
    lines += suggestions or [
        '    rename_segment_path(apps, "<Model>", "<old place>", "<new place>")'
    ]
    lines += [
        "        ),",
        "        migrations.RunPython.noop,",
        "    )",
        '  ("*" stands for a block id. Renaming only a block type, e.g. '
        '"image" -> "picture", moves nothing.)',
        "",
        "Then, and also if you added or removed a place on purpose, run:",
        "    python manage.py update_translation_snapshot",
    ]
    return "\n".join(lines)


class WagtailLocalizeIsolationTests(SimpleTestCase):
    def test_only_page_segments_imports_wagtail_localize(self):
        importers = set()
        for path in PROJECT.rglob("*.py"):
            relative = path.relative_to(PROJECT).as_posix()
            if (
                "/migrations/" in relative
                or "/tests/" in relative
                or relative.endswith("tests.py")
            ):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                if any(name.split(".")[0] == "wagtail_localize" for name in names):
                    importers.add(relative)
        self.assertEqual(
            importers - ALLOWED_IMPORTERS,
            set(),
            "Only translation/page_segments.py may import wagtail-localize. "
            "Use page_segments' functions instead.",
        )


class RenameSegmentPathTests(TestCase):
    def test_moves_stored_english(self):
        nb, _ = Locale.objects.get_or_create(language_code="nb")
        index = ArticleIndexPage(
            locale=nb, title="A", slug="a", section="info_articles"
        )
        Page.get_first_root_node().add_child(instance=index)
        article = ArticlePage(
            locale=nb,
            title="B",
            slug="b",
            published_date=timezone.now().date(),
            body=[("heading", {"text": "Program", "level": "h2"})],
        )
        index.add_child(instance=article)
        block_id = article.body[0].id
        segment = page_segments.Segment(f"body.{block_id}.text", "Program")
        stored_translations.save_machine(article, {segment: "Schedule"})

        stored_translations.rename_segment_path(
            apps, "ArticlePage", "body.*.text", "body.*.title"
        )
        self.assertEqual(
            SegmentTranslation.objects.get().segment_path, f"body.{block_id}.title"
        )
        stored_translations.rename_segment_path(apps, "ArticlePage", "body", "content")
        self.assertEqual(
            SegmentTranslation.objects.get().segment_path, f"content.{block_id}.title"
        )
