import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    """Schema step 1 of 3 for moving the title-banner fields off CategoryPage/
    ArticleIndexPage into their own model (see PageBannerStyle's own
    docstring) -- CreateModel only. Old fields on CategoryPage/
    ArticleIndexPage stay in place until 0103, so 0102's data migration has
    something to backfill from."""

    dependencies = [
        ("ifi_home_app", "0100_articleindexpage_banner_text_color_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="PageBannerStyle",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("translation_key", models.UUIDField(unique=True)),
                ("show_banner", models.BooleanField(default=False)),
                (
                    "banner_color",
                    models.CharField(
                        blank=True,
                        max_length=7,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$",
                                "Enter a valid hex color code, e.g. #ff8800 or #f80.",
                            )
                        ],
                    ),
                ),
                (
                    "banner_dot_color",
                    models.CharField(
                        blank=True,
                        max_length=7,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$",
                                "Enter a valid hex color code, e.g. #ff8800 or #f80.",
                            )
                        ],
                    ),
                ),
                (
                    "banner_text_color",
                    models.CharField(
                        blank=True,
                        max_length=7,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$",
                                "Enter a valid hex color code, e.g. #ff8800 or #f80.",
                            )
                        ],
                    ),
                ),
            ],
        ),
    ]
