"""Renames ArticleBlockStyle.box_text_color/box_text_custom_color to
text_color/text_custom_color -- text color turned out to apply independent
of whether a block's box is enabled (see _effective_heading_style() in
article_models.py), so the "box_" prefix no longer fit."""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0082_articleblockstyle_box_text_color_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="articleblockstyle",
            old_name="box_text_color",
            new_name="text_color",
        ),
        migrations.RenameField(
            model_name="articleblockstyle",
            old_name="box_text_custom_color",
            new_name="text_custom_color",
        ),
    ]
