from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0128_articleblockstyle_text_shadow_color_and_more"),
    ]

    operations = [
        # Existing signup_url data (in practice, almost always a Peoply
        # link) becomes peoply_url -- a rename preserves it as-is, no data
        # migration needed.
        migrations.RenameField(
            model_name="eventpage",
            old_name="signup_url",
            new_name="peoply_url",
        ),
        migrations.AlterField(
            model_name="eventpage",
            name="peoply_url",
            field=models.URLField(
                blank=True,
                help_text="Optional -- link to this event's page on Peoply.",
            ),
        ),
        # A new, separate, optional field for a non-Peoply signup link --
        # starts empty for every existing event.
        migrations.AddField(
            model_name="eventpage",
            name="signup_url",
            field=models.URLField(
                blank=True,
                default="",
                help_text="Optional -- link to a signup/registration form for this event, if not using Peoply.",
            ),
            preserve_default=False,
        ),
    ]
