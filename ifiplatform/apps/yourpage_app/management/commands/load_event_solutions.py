"""Loads the helpers' solutions from JSON on stdin, so the private file never
has to be in the repo or the image:

    docker compose exec -T web python manage.py load_event_solutions < solutions.json

The file is a list of {"issue": 12, "note": "...", "diff": "..."}. Running it
again updates the solutions by issue number instead of adding copies."""

import json
import sys

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from yourpage_app.models import EventSolution


class Command(BaseCommand):
    help = "Loads helper solutions from JSON on stdin (see the module docstring)."

    def handle(self, *args, **options):
        try:
            entries = json.load(sys.stdin)
        except ValueError as exc:
            raise CommandError(f"Not valid JSON: {exc}") from exc
        if not isinstance(entries, list):
            raise CommandError("Expected a JSON list of solutions.")

        with transaction.atomic():
            for entry in entries:
                try:
                    number = int(entry["issue"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise CommandError(
                        f"Entry without a valid 'issue': {entry!r}"
                    ) from exc
                EventSolution.objects.update_or_create(
                    issue_number=number,
                    defaults={
                        "note": entry.get("note", ""),
                        "diff": entry.get("diff", ""),
                    },
                )
        self.stdout.write(self.style.SUCCESS(f"Loaded {len(entries)} solution(s)."))
