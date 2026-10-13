from django.db import migrations


class Migration(migrations.Migration):
    """Schema step 3 of 3 -- see 0101/0102's own docstrings for the full
    sequence. Forward-only in spirit (like every other field-removal
    migration this session, see project memory on the SQLite reverse-
    migration gotcha) even though Django can technically reverse a plain
    RemoveField -- reversing would re-add these columns empty, not restore
    the values 0102 already migrated into PageBannerStyle."""

    dependencies = [
        ("ifi_home_app", "0102_backfill_pagebannerstyle"),
    ]

    operations = [
        migrations.RemoveField(model_name="articleindexpage", name="banner_color"),
        migrations.RemoveField(model_name="articleindexpage", name="banner_text_color"),
        migrations.RemoveField(model_name="articleindexpage", name="show_banner"),
        migrations.RemoveField(model_name="categorypage", name="banner_color"),
        migrations.RemoveField(model_name="categorypage", name="banner_text_color"),
        migrations.RemoveField(model_name="categorypage", name="show_banner"),
    ]
