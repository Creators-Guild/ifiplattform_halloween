"""MenuGroupLink.prefix -> label_prefix: a form field called "prefix"
shadows form.prefix in Wagtail's inline panel template, which broke the
Links panel in the menu group editor. Moves the stored English along."""

from django.db import migrations

from ifi_home_app.translation.stored_translations import rename_segment_path


class Migration(migrations.Migration):
    dependencies = [
        ("ifi_home_app", "0158_waiting_requested_by_person"),
    ]

    operations = [
        migrations.RenameField(
            model_name="menugrouplink",
            old_name="prefix",
            new_name="label_prefix",
        ),
        migrations.RunPython(
            lambda apps, schema_editor: rename_segment_path(
                apps, "MenuGroupLink", "prefix", "label_prefix"
            ),
            migrations.RunPython.noop,
        ),
    ]
