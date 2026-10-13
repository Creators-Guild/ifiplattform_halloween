from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0143_backfill_articlepage_published_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="articlepage",
            name="published_date",
            field=models.DateField(),
        ),
    ]
