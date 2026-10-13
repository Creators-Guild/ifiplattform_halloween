"""Register every English MenuGroup copy that isn't yet a wagtail-localize
translation of its nb group (e.g. the ones migration 0152_menus created),
so English menus are edited through the translation editor and synced from
nb. Safe to re-run: already-linked groups are skipped."""

from django.core.management.base import BaseCommand
from wagtail.models import Locale
from wagtail_localize.models import Translation

from ifiplatform.apps.ifi_home_app.models.menus import MenuGroup
from ifiplatform.apps.ifi_home_app.translation.snippets import link_existing_translation
from ifiplatform.apps.ifi_home_app.translation.sync import SOURCE_LANGUAGE_CODE


class Command(BaseCommand):
    help = "Links existing translated MenuGroup copies to their nb source in wagtail-localize."

    def handle(self, *args, **options):
        source_locale = Locale.objects.get(language_code=SOURCE_LANGUAGE_CODE)
        linked = skipped = 0
        for group in MenuGroup.objects.filter(locale=source_locale):
            for translated in MenuGroup.objects.filter(
                translation_key=group.translation_key
            ).exclude(locale=source_locale):
                already = Translation.objects.filter(
                    source__object_id=group.translation_key,
                    target_locale=translated.locale,
                ).exists()
                if already:
                    skipped += 1
                    continue
                link_existing_translation(group, translated)
                linked += 1
                self.stdout.write(
                    f"  linked {group.title} -> {translated.title} ({translated.locale})"
                )
        self.stdout.write(
            self.style.SUCCESS(f"Done: {linked} linked, {skipped} already linked.")
        )
