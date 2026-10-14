"""Pushes ifi_home_app/translation/glossary_terms.py's nb -> en term list to
DeepL as a glossary, so DeepL honours those exact translations (or "don't
translate this") on every machine-translation call this project makes --
everything goes through translation/deepl.py's translate_texts(), so one
glossary covers it all.

DeepL's v2 glossaries are immutable once created (no "update entries"
endpoint) -- this command deletes any existing glossary with the same name
before creating a fresh one from the current term list, so it's safe to
re-run whenever glossary_terms.py changes.

By default, just prints the new glossary_id -- copy it into
DEEPL_GLOSSARY_ID in .env (same copy-paste flow as DJANGO_SECRET_KEY in
README.md's setup steps) and restart the server; settings.py reads it from
there as DEEPL_GLOSSARY_ID.
--write-env does that .env edit itself instead -- used by deploy/deploy.sh so
production never needs that manual step (a stale DEEPL_GLOSSARY_ID is what
caused a real KeyError: 'translations' machine-translation outage once).

Also records the sync time via GlossarySyncState, so the nightly
translate_english run knows which DeepL translations predate this glossary
version and redoes them (stored_translations.forget_stale_glossary_rows)."""

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ifi_home_app.translation.glossary_terms import GLOSSARY_TERMS
from ifi_home_app.models import GlossarySyncState

GLOSSARY_NAME = "ifiplatform-nb-en"
SOURCE_LANG = "NB"
TARGET_LANG = "EN"


class Command(BaseCommand):
    help = (
        "Pushes deepl_glossary_terms.py's nb -> en term list to DeepL as a "
        "glossary (deleting and recreating any existing one with the same "
        "name, since DeepL glossaries can't be edited in place). Prints the "
        "resulting glossary_id -- copy it into DEEPL_GLOSSARY_ID in .env, "
        "or pass --write-env to have this command do that edit itself."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--write-env",
            action="store_true",
            help="Rewrite DEEPL_GLOSSARY_ID in .env to the new glossary_id "
            "instead of just printing it. Still requires a server "
            "restart to take effect.",
        )

    def handle(self, *args, **options):
        auth_key = settings.DEEPL_API_KEY
        if not auth_key:
            raise CommandError("DEEPL_API_KEY is not set in .env.")

        api_base = (
            "https://api-free.deepl.com"
            if auth_key.endswith(":fx")
            else "https://api.deepl.com"
        )
        headers = {"Authorization": f"DeepL-Auth-Key {auth_key}"}

        existing = requests.get(f"{api_base}/v2/glossaries", headers=headers)
        existing.raise_for_status()
        for glossary in existing.json()["glossaries"]:
            if glossary["name"] == GLOSSARY_NAME:
                requests.delete(
                    f"{api_base}/v2/glossaries/{glossary['glossary_id']}",
                    headers=headers,
                ).raise_for_status()
                self.stdout.write(f"Deleted old glossary {glossary['glossary_id']}")

        entries = "\n".join(f"{nb}\t{en}" for nb, en in GLOSSARY_TERMS.items())
        response = requests.post(
            f"{api_base}/v2/glossaries",
            headers=headers,
            json={
                "name": GLOSSARY_NAME,
                "source_lang": SOURCE_LANG,
                "target_lang": TARGET_LANG,
                "entries": entries,
                "entries_format": "tsv",
            },
        )
        response.raise_for_status()
        glossary_id = response.json()["glossary_id"]
        GlossarySyncState.touch()

        self.stdout.write(
            self.style.SUCCESS(
                f"Created glossary {glossary_id} with {len(GLOSSARY_TERMS)} term(s)."
            )
        )

        if options["write_env"]:
            self._write_env(glossary_id)
            self.stdout.write(
                self.style.SUCCESS(
                    "DEEPL_GLOSSARY_ID updated in .env -- restart the server to pick it up."
                )
            )
        else:
            self.stdout.write(
                f"Now set DEEPL_GLOSSARY_ID={glossary_id} in .env and restart the server."
            )

    def _write_env(self, glossary_id):
        env_path = settings.BASE_DIR / ".env"
        if not env_path.exists():
            raise CommandError(f"--write-env: no .env file found at {env_path}")

        lines = env_path.read_text(encoding="utf-8").splitlines(keepends=True)
        new_line = f"DEEPL_GLOSSARY_ID={glossary_id}\n"
        for i, line in enumerate(lines):
            if line.startswith("DEEPL_GLOSSARY_ID="):
                lines[i] = new_line
                break
        else:
            lines.append(new_line)
        env_path.write_text("".join(lines), encoding="utf-8")
