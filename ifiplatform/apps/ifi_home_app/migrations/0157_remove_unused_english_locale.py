"""Fresh databases (new setups, CI, tests) get an "en" locale from 0039,
but since the switch to one Norwegian tree nothing uses it. Deleted here
when unused; on databases with English content it's left for
`manage.py switch_to_english_overlay` (run by deploy.sh). Forward-only."""

from django.db import migrations


def remove_unused_english_locale(apps, schema_editor):
    Locale = apps.get_model("wagtailcore", "Locale")
    english = Locale.objects.filter(language_code="en").first()
    if english is None:
        return
    for model in apps.get_models():
        for field in model._meta.fields:
            if field.is_relation and field.related_model is Locale:
                if model._default_manager.filter(**{field.name: english}).exists():
                    return
    english.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0156_waiting_for_english_and_translation_settings"),
        ("wagtail_localize", "0016_rename_page_revision_translationlog_revision"),
    ]

    operations = [
        migrations.RunPython(remove_unused_english_locale, migrations.RunPython.noop),
    ]
