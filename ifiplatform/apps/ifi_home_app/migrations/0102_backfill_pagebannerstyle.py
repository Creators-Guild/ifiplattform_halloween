from django.db import migrations

TEXT_COLOR_HEX = {"light": "#fffff9", "dark": "#120e0e"}


def backfill(apps, schema_editor):
    PageBannerStyle = apps.get_model("ifi_home_app", "PageBannerStyle")
    connection = schema_editor.connection

    # translation_key -> (banner_color, banner_text_color) for the row we're
    # keeping -- nb wins on conflict (see this migration's own docstring),
    # matching this session's established convention.
    chosen = {}
    with connection.cursor() as cursor:
        for table in ("ifi_home_app_categorypage", "ifi_home_app_articleindexpage"):
            # a bound param (not a hardcoded "= 1") so each backend's own
            # adapter translates Python True correctly -- SQLite stores
            # booleans as 0/1 and accepts "= 1" as a literal, but
            # PostgreSQL has a real boolean type and rejects comparing it
            # to an integer outright ("operator does not exist: boolean =
            # integer"). Caught when this hit production (Postgres) after
            # working fine against the SQLite dev DB.
            cursor.execute(
                f"""
                SELECT p.translation_key, l.language_code, c.banner_color, c.banner_text_color
                FROM {table} c
                JOIN wagtailcore_page p ON p.id = c.page_ptr_id
                JOIN wagtailcore_locale l ON l.id = p.locale_id
                WHERE c.show_banner = %s
                """,
                [True],
            )
            for (
                translation_key,
                language_code,
                banner_color,
                banner_text_color,
            ) in cursor.fetchall():
                is_nb = language_code == "nb"
                if translation_key not in chosen or is_nb:
                    chosen[translation_key] = (banner_color, banner_text_color)

    for translation_key, (banner_color, banner_text_color) in chosen.items():
        PageBannerStyle.objects.update_or_create(
            translation_key=translation_key,
            defaults={
                "show_banner": True,
                "banner_color": banner_color,
                "banner_dot_color": "",
                "banner_text_color": TEXT_COLOR_HEX.get(banner_text_color, "#fffff9"),
            },
        )


def unbackfill(apps, schema_editor):
    """Reverse: delete every PageBannerStyle row this migration created.
    Safe -- 0101 (CreateModel) is the only thing before this in the chain,
    nothing else could have created rows yet at this point in the history."""
    PageBannerStyle = apps.get_model("ifi_home_app", "PageBannerStyle")
    PageBannerStyle.objects.all().delete()


class Migration(migrations.Migration):
    """Schema step 2 of 3 -- see 0101/0103's own docstrings for the full
    sequence. Backfills PageBannerStyle from the still-present old
    show_banner/banner_color/banner_text_color fields on CategoryPage/
    ArticleIndexPage (removed next, in 0103). Verified against the real dev
    DB before writing this: 4 rows currently have show_banner=True across
    both models, two genuine translation conflicts (nb has it on, en
    doesn't) resolved nb-wins, matching this session's established
    convention (see ArticlePage.publish_target / the ArticleStyle backfill
    in migration 0095). The old banner_text_color choice ('light'/'dark')
    is converted to a hex here (#fffff9/#120e0e, matching --color-bright/
    --color-ink in tokens.css) -- banner_dot_color has no old equivalent,
    left blank (falls back to white at render time)."""

    dependencies = [
        ("ifi_home_app", "0101_pagebannerstyle"),
    ]

    operations = [
        migrations.RunPython(backfill, unbackfill),
    ]
