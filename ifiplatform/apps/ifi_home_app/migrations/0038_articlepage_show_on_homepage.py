from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0037_remove_articlepage_show_on_homepage"),
    ]

    operations = [
        migrations.AddField(
            model_name="articlepage",
            name="show_on_homepage",
            field=models.BooleanField(
                default=True,
                help_text="Whether this article can be suggested on the homepage (newsbar/articles bar).",
            ),
        ),
    ]
