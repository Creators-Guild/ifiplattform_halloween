from django.db import migrations

LANGUAGE_CODES = ["en", "nb"]


def create_missing_locales(apps, schema_editor):
    Locale = apps.get_model("wagtailcore", "Locale")
    for language_code in LANGUAGE_CODES:
        Locale.objects.get_or_create(language_code=language_code)


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0038_articlepage_show_on_homepage"),
        ("wagtailcore", "0097_baselogentry_uuid_action_timestamp_indexes"),
    ]

    operations = [
        migrations.RunPython(create_missing_locales, migrations.RunPython.noop),
    ]
