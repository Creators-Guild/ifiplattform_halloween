"""Schema step 1 of 3 for re-keying ArticleBlockStyle from a per-page FK
(article) to a per-translation UUID (translation_key), so per-block style
overrides are automatically shared across every locale copy of an article
instead of being independently set per page -- see the follow-up data
migration (0092) for why, and the final schema step (0093) that drops
`article` and makes `translation_key` required once every row has one.

Nullable/still-has-article here on purpose: this only adds the new column
and loosens `article` to nullable so the data migration has somewhere
consistent to write into and read from; no existing data is touched yet.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0090_fix_revision_content_type_and_body_shape"),
    ]

    operations = [
        migrations.AddField(
            model_name="articleblockstyle",
            name="translation_key",
            field=models.UUIDField(null=True),
        ),
        migrations.AlterField(
            model_name="articleblockstyle",
            name="article",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="block_styles",
                to="ifi_home_app.articlepage",
            ),
        ),
    ]
