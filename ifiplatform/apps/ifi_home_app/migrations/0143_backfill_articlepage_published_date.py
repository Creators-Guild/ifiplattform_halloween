"""Backfills ArticlePage.published_date for any existing row that's still
NULL (today's date, a safe placeholder) before the next migration makes
the column NOT NULL -- published_date is becoming a required field.
"""

from django.db import migrations
from django.utils import timezone


def backfill(apps, schema_editor):
    ArticlePage = apps.get_model("ifi_home_app", "ArticlePage")
    ArticlePage.objects.filter(published_date__isnull=True).update(
        published_date=timezone.now().date()
    )


def unbackfill(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0142_unionspendingpeoplylink_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill, unbackfill),
    ]
