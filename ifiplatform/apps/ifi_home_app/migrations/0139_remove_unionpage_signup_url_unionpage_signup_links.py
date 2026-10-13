"""Data migration: signup_url (a single URLField) is replaced by
signup_links (a StreamField of {label, url} pairs, so a union can list
several sign-up/interest links with their own editor-chosen labels instead
of one fixed "Sign up / register interest" link -- see unions.py).

Any existing signup_url value is carried over as a single signup_links
entry (same label the old link used to show) before the old column is
dropped -- AddField/RunPython/RemoveField in that order within this one
migration, so the historical model this RunPython step sees still has
signup_url (not yet removed) alongside the just-added signup_links (see
0077_unwrap_box_blocks.py for the same raw-list-assignment approach on a
brand-new/empty StreamField; unlike 0089_merge_paragraph_styled_text.py's
raw-SQL workaround, there's no existing signup_links content whose block
types could be silently dropped by StreamField.to_python here -- this only
ever writes one new block per page, never rewrites existing StreamField
data)."""

import uuid

from django.db import migrations

import wagtail.fields


def copy_signup_url_to_signup_links(apps, schema_editor):
    UnionPage = apps.get_model("ifi_home_app", "UnionPage")
    for page in UnionPage.objects.exclude(signup_url=""):
        page.signup_links = [
            {
                "type": "link",
                "value": {
                    "label": "Sign up / register interest",
                    "url": page.signup_url,
                },
                "id": str(uuid.uuid4()),
            }
        ]
        page.save()


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0138_alter_unionpage_sitting_members"),
    ]

    operations = [
        migrations.AddField(
            model_name="unionpage",
            name="signup_links",
            field=wagtail.fields.StreamField(
                [("link", 2)],
                blank=True,
                block_lookup={
                    0: (
                        "wagtail.blocks.CharBlock",
                        (),
                        {
                            "help_text": 'e.g. "Bli medlem", "Meld interesse", "Søk verv".'
                        },
                    ),
                    1: ("wagtail.blocks.URLBlock", (), {}),
                    2: ("wagtail.blocks.StructBlock", [[("label", 0), ("url", 1)]], {}),
                },
                help_text="Optional -- one or more sign-up/interest links, each with its own label (e.g. a membership form, a volunteer sign-up).",
            ),
        ),
        migrations.RunPython(
            copy_signup_url_to_signup_links, migrations.RunPython.noop
        ),
        migrations.RemoveField(
            model_name="unionpage",
            name="signup_url",
        ),
    ]
