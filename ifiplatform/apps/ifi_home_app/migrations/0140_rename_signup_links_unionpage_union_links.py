from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0139_remove_unionpage_signup_url_unionpage_signup_links"),
    ]

    operations = [
        migrations.RenameField(
            model_name="unionpage",
            old_name="signup_links",
            new_name="union_links",
        ),
    ]
