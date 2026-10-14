"""Creates the "Helpers" group: its members see the event solutions on the
issue board (yourpage_app.permissions.can_see_solutions). It holds no
permissions itself -- organisers add helpers to it in /admin/."""

from django.db import migrations


def create_group(apps, schema_editor):
    apps.get_model("auth", "Group").objects.get_or_create(name="Helpers")


def delete_group(apps, schema_editor):
    apps.get_model("auth", "Group").objects.filter(name="Helpers").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("yourpage_app", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_group, delete_group)]
